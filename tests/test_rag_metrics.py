"""RAG quality checks via RAGAS — non-deterministic (a real model answers,
real embeddings), requires reachable mlx_lm.server + mlx-omni-server. Slower
than the pure unit tests, run on its own: `pytest tests/test_rag_metrics.py`.

The RAG pipeline itself still only exists as a prototype in `r&d.ipynb`
(Steps 13-15), not yet in `finanalyticsagent/` — this test rebuilds it
inline rather than importing a module that doesn't exist yet. Once RAG is
extracted into the package, this should import from there instead.

Uses ragas 0.4.3's current ("collections") metric API, not the older
`ragas.metrics`/`evaluate()` path — that older path is deprecated in this
version. Two ragas quirks worth remembering if this breaks on upgrade:
- ragas 0.4.3 imports `ChatVertexAI` from a `langchain_community` path that
  no longer exists post-sunset — the `sys.modules` stub below works around
  it; we never use VertexAI.
- `Faithfulness`/`FactualCorrectness` (LLM-judge metrics) hit the same
  hidden-`<think>`-reasoning-eats-max_tokens problem as our own agent
  (`graph.answer_was_truncated`) — even with `max_tokens` raised, they were
  too slow/unreliable on our 8B local model to depend on in a test suite,
  so only the non-LLM metric is asserted here. Documented, not chased
  further, matching this project's "don't fix a hypothetical problem"
  stance — see CLAUDE.md.
"""

import sys
import types

# Must run before importing ragas — see module docstring.
_stub = types.ModuleType("langchain_community.chat_models.vertexai")
_stub.ChatVertexAI = type("ChatVertexAI", (), {})
sys.modules["langchain_community.chat_models.vertexai"] = _stub

import pandas as pd
import pymupdf
import pytest
from docx import Document as DocxDocument
from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ragas.metrics.collections import NonLLMStringSimilarity

from finanalyticsagent import active_table
from finanalyticsagent.prompts import build_system_prompt
from finanalyticsagent.tools import create_chart, execute_python_code

EVAL_QUESTIONS = [
    {
        "question": "In Taj al-Muluk's story, what was the price of the finest bolt of dibaj?",
        "reference": "The finest bolt of dibaj was priced at two hundred and fifty dinars.",
    },
    {
        "question": "According to Aziz's reckoning, what was the total value of the day's trade?",
        "reference": "The total value of the day's trade was one thousand one hundred and sixty dinars.",
    },
    {
        "question": "What reward did the hammam keeper receive from King Omar bin al-Nu'uman?",
        "reference": "The hammam keeper received 120 dinars and a stall in the Forty Thieves Foundry market, free of guild dues for ten years.",
    },
]

# Minimum acceptable non-LLM string similarity between the agent's answer and
# a known-correct reference. Not tuned/rigorous — a coarse floor, since the
# agent's phrasing (markdown bold, digits vs words) always differs somewhat
# from the reference even when factually correct. See module docstring.
MIN_STRING_SIMILARITY = 0.25


@pytest.fixture(scope="module")
def rag_agent():
    model = ChatOpenAI(
        model="Qwen/Qwen3-8B-MLX-4bit",
        base_url="http://10.195.19.15:8000/v1",
        api_key="dummy",
        temperature=0,
        max_tokens=8192,
    )

    dfs = {
        "caravan_accounts": pd.read_csv("bazaar_books/caravan_accounts.csv"),
        "guild_ledger": pd.read_csv("bazaar_books/guild_ledger.csv"),
        "realm_metadata": pd.read_csv("bazaar_books/realm_metadata.csv"),
    }
    active_table.set_tables(dfs)

    embeddings = OpenAIEmbeddings(
        model="mlx-community/Qwen3-Embedding-0.6B-mxfp8",
        base_url="http://10.195.19.15:8090/v1",
        api_key="dummy",
        check_embedding_ctx_length=False,
    )

    def load_pdf(path):
        with pymupdf.open(path) as pdf:
            return "\n".join(page.get_text() for page in pdf)

    def load_docx(path):
        doc = DocxDocument(path)
        return "\n".join(p.text for p in doc.paragraphs)

    document_files = {
        "zau_al_makan_decree.docx": load_docx("bazaar_books/zau_al_makan_decree.docx"),
        "hammam_keeper_proclamation.pdf": load_pdf("bazaar_books/hammam_keeper_proclamation.pdf"),
        "taj_al_muluk_bazaar.docx": load_docx("bazaar_books/taj_al_muluk_bazaar.docx"),
        "aziz_reckoning.pdf": load_pdf("bazaar_books/aziz_reckoning.pdf"),
    }

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts, metadatas = [], []
    for source, full_text in document_files.items():
        for chunk in splitter.split_text(full_text):
            texts.append(chunk)
            metadatas.append({"source": source})

    vectorstore = Chroma.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)

    @tool
    def search_documents(query: str) -> str:
        """Search the loaded non-tabular documents for relevant text."""
        hits = vectorstore.similarity_search(query, k=5)
        return "\n---\n".join(f"[{h.metadata['source']}] {h.page_content}" for h in hits)

    document_names = "\n".join(f"- {name}" for name in document_files)
    system_prompt = build_system_prompt(dfs) + f"\n\n## Documents available\n\n{document_names}\n"

    return create_agent(
        model=model,
        tools=[execute_python_code, create_chart, search_documents],
        system_prompt=system_prompt,
    )


@pytest.mark.parametrize("item", EVAL_QUESTIONS, ids=[q["question"][:40] for q in EVAL_QUESTIONS])
@pytest.mark.asyncio
async def test_answer_matches_reference_above_floor(rag_agent, item):
    result = rag_agent.invoke({"messages": [{"role": "user", "content": item["question"]}]})
    response = result["messages"][-1].content.strip()

    metric = NonLLMStringSimilarity()
    score = await metric.ascore(response=response, reference=item["reference"])

    assert score.value >= MIN_STRING_SIMILARITY, (
        f"Answer too dissimilar from reference (score={score.value:.3f}): {response!r}"
    )
