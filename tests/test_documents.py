"""Unit tests for finanalyticsagent.documents: pure, deterministic, no LLM/embedding calls."""

from pathlib import Path

import pytest

from finanalyticsagent import documents


def test_get_vectorstore_raises_when_nothing_was_set():
    documents.set_vectorstore(None)
    with pytest.raises(RuntimeError):
        documents.get_vectorstore()


def test_set_vectorstore_then_get_vectorstore_returns_the_same_object():
    fake_store = object()

    documents.set_vectorstore(fake_store)

    assert documents.get_vectorstore() is fake_store


def test_load_pdf_extracts_text():
    text = documents.load_pdf("bazaar_books/hammam_keeper_proclamation.pdf")
    assert "hammam" in text.lower()


def test_load_docx_extracts_text():
    text = documents.load_docx("bazaar_books/zau_al_makan_decree.docx")
    assert "Zau al-Makan" in text


def test_chunk_documents_respects_chunk_size_and_tags_source():
    long_text = "word " * 300  # long enough to require multiple chunks at CHUNK_SIZE=500
    texts, metadatas = documents._chunk_documents({"some_file.docx": long_text})

    assert len(texts) > 1
    assert all(len(chunk) <= documents.CHUNK_SIZE for chunk in texts)
    assert all(m == {"source": "some_file.docx"} for m in metadatas)


def test_reset_knowledge_base_leaves_an_empty_persist_dir():
    documents.reset_knowledge_base()

    assert Path(documents.PERSIST_DIR).is_dir()
    assert list(Path(documents.PERSIST_DIR).iterdir()) == []
