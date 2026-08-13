"""Non-tabular document knowledge base: loading, chunking, embeddings, Chroma.

Mirrors `active_table.py`'s role for `dfs` — this module holds the single
source of truth for RAG config (chunk size, k, embedding model, persistence
paths) plus the currently active vectorstore, so `tools.py`, `graph.py`,
`r&d.ipynb`, and `tests/` all read the same values instead of each
hardcoding their own copy.

Persistence model: `build_knowledge_base` READS an existing persisted
collection if one is already on disk, and only creates it if missing —
it does not wipe on every call. Wiping (`reset_knowledge_base`) is a
separate, explicitly-called operation, not part of the normal load path.
"""

import os
import shutil
from pathlib import Path

import pymupdf
from chromadb.api.client import SharedSystemClient
from docx import Document as DocxDocument
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
SEARCH_K = 5
PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "bazaar_books_kb"
# Defaults match this project's own local mlx-omni-server setup — override
# via .env (see .env.example) to point elsewhere.
EMBEDDINGS_MODEL_NAME = os.getenv("EMBEDDINGS_MODEL", "mlx-community/Qwen3-Embedding-0.6B-mxfp8")
EMBEDDINGS_BASE_URL = os.getenv("EMBEDDINGS_BASE_URL", "http://10.195.19.15:8090/v1")

embeddings = OpenAIEmbeddings(
    model=EMBEDDINGS_MODEL_NAME,
    base_url=EMBEDDINGS_BASE_URL,
    api_key=os.getenv("EMBEDDINGS_API_KEY", "dummy"),
    check_embedding_ctx_length=False,  # mlx-omni-server expects a raw string, not token ids
)

# The demo document set used to seed/restore the canonical persisted
# knowledge base (see ensure_canonical_knowledge_base) — same 4 files used
# throughout r&d.ipynb Steps 15-20.
CANONICAL_DOCUMENTS = {
    "zau_al_makan_decree.docx": "bazaar_books/zau_al_makan_decree.docx",
    "hammam_keeper_proclamation.pdf": "bazaar_books/hammam_keeper_proclamation.pdf",
    "taj_al_muluk_bazaar.docx": "bazaar_books/taj_al_muluk_bazaar.docx",
    "aziz_reckoning.pdf": "bazaar_books/aziz_reckoning.pdf",
}

_active_vectorstore: Chroma | None = None
_active_source_filter: list[str] | None = None


def load_pdf(path: str) -> str:
    """Extract all text from a PDF file.

    Args:
        path: path to a .pdf file.

    Returns:
        The concatenated text of every page.
    """
    with pymupdf.open(path) as pdf:
        return "\n".join(page.get_text() for page in pdf)


def load_docx(path: str) -> str:
    """Extract all paragraph text from a .docx file.

    Args:
        path: path to a .docx file.

    Returns:
        The concatenated text of every paragraph.
    """
    doc = DocxDocument(path)
    return "\n".join(p.text for p in doc.paragraphs)


def _chunk_documents(document_files: dict[str, str]) -> tuple[list[str], list[dict]]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    texts, metadatas = [], []
    for source, full_text in document_files.items():
        for chunk in splitter.split_text(full_text):
            texts.append(chunk)
            metadatas.append({"source": source})
    return texts, metadatas


def build_knowledge_base(document_files: dict[str, str], persist: bool = True) -> Chroma:
    """Build or reload the document knowledge base.

    If `persist` is True and a NON-EMPTY collection already exists on disk
    at `PERSIST_DIR`/`COLLECTION_NAME`, this reloads it (no re-embedding, no
    duplication) rather than rebuilding from `document_files` — matching
    Chroma's own "reload via a fresh client" behavior. If nothing exists
    yet — or the directory exists but is empty, e.g. right after
    `reset_knowledge_base()` — it embeds `document_files` and persists them.
    (Checking directory existence alone is not enough: an empty
    `persist_directory` still "exists", and reloading it would silently
    return a knowledge base with zero documents instead of building one.)

    Args:
        document_files: mapping of source file name to its full extracted
            text (as returned by load_pdf/load_docx).
        persist: whether to write to/read from disk (PERSIST_DIR). False
            builds a purely in-memory store instead (e.g. for evaluation
            runs that don't want to touch the shared knowledge base).

    Returns:
        The Chroma vectorstore, ready for `.similarity_search(...)`.
    """
    if persist and Path(PERSIST_DIR).exists():
        existing = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=PERSIST_DIR,
        )
        if existing._collection.count() > 0:
            return existing

    texts, metadatas = _chunk_documents(document_files)
    kwargs = {"texts": texts, "embedding": embeddings, "metadatas": metadatas}
    if persist:
        kwargs["collection_name"] = COLLECTION_NAME
        kwargs["persist_directory"] = PERSIST_DIR
    return Chroma.from_texts(**kwargs)


def list_persisted_sources() -> list[str]:
    """List the distinct source file names already in the persisted knowledge base.

    Returns:
        Sorted list of source names (from chunk metadata), or an empty list
        if `PERSIST_DIR` doesn't exist or the collection is empty.
    """
    if not Path(PERSIST_DIR).exists():
        return []
    existing = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR,
    )
    if existing._collection.count() == 0:
        return []
    sources = {m["source"] for m in existing.get()["metadatas"] if m and "source" in m}
    return sorted(sources)


def ensure_canonical_knowledge_base() -> Chroma:
    """Reload the persisted knowledge base, seeding it from CANONICAL_DOCUMENTS if empty.

    Self-healing: rather than surfacing an empty knowledge base (e.g. after
    `reset_knowledge_base()` or a test run that wiped it), this rebuilds it
    from the known synthetic demo documents so the app always has a
    reference knowledge base to fall back on.

    Returns:
        The Chroma vectorstore, ready for `.similarity_search(...)`.
    """
    if list_persisted_sources():
        return build_knowledge_base({}, persist=True)

    document_files = {
        name: (load_pdf(path) if path.endswith(".pdf") else load_docx(path))
        for name, path in CANONICAL_DOCUMENTS.items()
    }
    return build_knowledge_base(document_files, persist=True)


def set_source_filter(sources: list[str] | None) -> None:
    """Restrict search_documents to only the given source file names.

    Args:
        sources: source file names to allow, or None to search everything
            in the active vectorstore.
    """
    global _active_source_filter
    _active_source_filter = sources


def get_source_filter() -> list[str] | None:
    """Get the current source-name restriction for search_documents.

    Returns:
        The list set by the most recent call to set_source_filter, or None.
    """
    return _active_source_filter


def add_documents(vectorstore: Chroma, document_files: dict[str, str]) -> None:
    """Chunk and add new documents to an existing vectorstore (e.g. on upload).

    Args:
        vectorstore: the Chroma instance to add to.
        document_files: mapping of source file name to its full extracted text.
    """
    texts, metadatas = _chunk_documents(document_files)
    vectorstore.add_texts(texts=texts, metadatas=metadatas)


def reset_knowledge_base() -> None:
    """Wipe the persisted knowledge base from disk.

    Only needed when deliberately starting over (e.g. a "reset" action in
    the app or a test setup). chromadb caches clients per-process
    (`SharedSystemClient`) — without clearing that cache, a client created
    against this path later in the same process can reuse a stale
    connection to the now-deleted database and fail with "attempt to write
    a readonly database" (verified: reproduces exactly, fix confirmed).
    """
    shutil.rmtree(PERSIST_DIR, ignore_errors=True)
    Path(PERSIST_DIR).mkdir(exist_ok=True)
    SharedSystemClient.clear_system_cache()


def set_vectorstore(vectorstore: Chroma) -> None:
    """Set the vectorstore that tools should search against.

    Args:
        vectorstore: the Chroma instance to make active.
    """
    global _active_vectorstore
    _active_vectorstore = vectorstore


def get_vectorstore() -> Chroma:
    """Get the currently active vectorstore.

    Returns:
        The vectorstore set by the most recent call to set_vectorstore.

    Raises:
        RuntimeError: if no vectorstore has been set yet.
    """
    if _active_vectorstore is None:
        raise RuntimeError("No document knowledge base loaded yet — call set_vectorstore(...) first.")
    return _active_vectorstore
