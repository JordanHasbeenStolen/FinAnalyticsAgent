"""RAG quality checks via RAGAS — non-deterministic (a real model answers,
real embeddings), requires reachable mlx_lm.server + mlx-omni-server. Slower
than the pure unit tests, run on its own: `pytest tests/test_rag_metrics.py`.

Builds the agent via `finanalyticsagent.graph.build_agent(tables,
document_files)` — the real RAG pipeline, not a reimplementation. Uses an
in-memory knowledge base (`persist=False`) so this test never touches the
shared `chroma_db/` on disk.

Uses ragas 0.4.3's current ("collections") metric API, not the older
`ragas.metrics`/`evaluate()` path — that older path is deprecated in this
version. Two ragas quirks worth remembering if this breaks on upgrade:
- ragas 0.4.3 imports `ChatVertexAI` from a `langchain_community` path that
  no longer exists (that class moved to `langchain-google-vertexai`) — the
  `sys.modules` stub below works around it; we never use VertexAI.
- `Faithfulness`/`FactualCorrectness` (LLM-judge metrics) hit the same
  hidden-`<think>`-reasoning-eats-max_tokens problem as our own agent
  (`graph.answer_was_truncated`) — even with `max_tokens` raised, they were
  too slow/unreliable on our 8B local Qwen3 model to depend on in a test
  suite, so only the non-LLM metric is asserted here. This is specifically
  a judge-model problem, not a RAG-pipeline problem: revisit with a larger
  or cloud-hosted judge model (at minimum DeepSeek-class, not Qwen3-8B) if
  LLM-judge scoring is ever needed — the small local model's hidden
  reasoning is the blocker, not the metric itself. Documented, not chased
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
import pytest
from ragas.metrics.collections import NonLLMStringSimilarity

from finanalyticsagent import documents
from finanalyticsagent.graph import build_agent

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
    dfs = {
        "caravan_accounts": pd.read_csv("bazaar_books/caravan_accounts.csv"),
        "guild_ledger": pd.read_csv("bazaar_books/guild_ledger.csv"),
        "realm_metadata": pd.read_csv("bazaar_books/realm_metadata.csv"),
    }

    document_files = {
        "zau_al_makan_decree.docx": documents.load_docx("bazaar_books/zau_al_makan_decree.docx"),
        "hammam_keeper_proclamation.pdf": documents.load_pdf("bazaar_books/hammam_keeper_proclamation.pdf"),
        "taj_al_muluk_bazaar.docx": documents.load_docx("bazaar_books/taj_al_muluk_bazaar.docx"),
        "aziz_reckoning.pdf": documents.load_pdf("bazaar_books/aziz_reckoning.pdf"),
    }

    return build_agent(dfs, document_files, persist_documents=False)


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
