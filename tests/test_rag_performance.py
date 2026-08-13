"""RAG/agent performance measurement — latency and tokens/sec per question.

Educational, not a strict benchmark: local model performance on a single
Mac varies a lot run-to-run (thermal state, what else is running, etc.), so
this asserts only generous sanity ceilings, not tight SLAs. The point is to
have the numbers captured every time the suite runs, so a real regression
(e.g. a prompt change that makes every answer 3x slower) shows up instead
of going unnoticed.

Requires reachable mlx_lm.server + mlx-omni-server. Slow — real network
calls, no mocking (see CLAUDE.md: this project always tests against the
real backend, not a stub).

**What "tokens/sec" actually means here:** `response_metadata["token_usage"]`
comes straight from the server (mlx_lm.server reports it, same shape as
OpenAI's API) — `completion_tokens` is how many tokens the model generated
for its final answer. We time the whole `agent.invoke(...)` call ourselves
with `time.perf_counter()` and divide. This is a coarse per-question rate,
not the model's raw decode speed — it also includes tool-call round trips
(e.g. `execute_python_code`, `search_documents`), which take their own
time and don't produce "model tokens" at all. A ReAct question that calls a
tool will look "slower per token" than a no-tool question for this reason,
not because the model itself is slower — that's expected, not a bug.
"""

import time

import pandas as pd
import pytest

from finanalyticsagent import active_table, documents
from finanalyticsagent.graph import build_agent

QUESTIONS = {
    "tabular (execute_python_code)": "Which realm had the highest net income?",
    "document (search_documents)": "In Taj al-Muluk's story, what was the price of the finest bolt of dibaj?",
    "small talk (no tool)": "Hello! How are you?",
}

# Generous ceilings, not real SLAs — see module docstring. Loosely based on
# CLAUDE.md's own measured worst case (a heavy 3-table transitive join took
# 286.9s end to end); a single-tool or no-tool question should never come
# close to that on this hardware.
MAX_SECONDS = 120


@pytest.fixture(scope="module")
def dfs():
    return {
        "caravan_accounts": pd.read_csv("bazaar_books/caravan_accounts.csv"),
        "guild_ledger": pd.read_csv("bazaar_books/guild_ledger.csv"),
        "realm_metadata": pd.read_csv("bazaar_books/realm_metadata.csv"),
    }


@pytest.fixture(scope="module")
def perf_agent(dfs):
    document_files = {
        "taj_al_muluk_bazaar.docx": documents.load_docx("bazaar_books/taj_al_muluk_bazaar.docx"),
    }
    return build_agent(dfs, document_files, persist_documents=False)


@pytest.fixture
def restore_tables(dfs):
    """Undo conftest.py's per-test active_table wipe for this module-scoped agent."""
    active_table.set_tables(dfs)


@pytest.mark.parametrize("label, question", QUESTIONS.items(), ids=list(QUESTIONS))
def test_latency_and_throughput(perf_agent, restore_tables, label, question):
    start = time.perf_counter()
    result = perf_agent.invoke({"messages": [{"role": "user", "content": question}]})
    elapsed = time.perf_counter() - start

    # Sum completion_tokens across every AI message in this turn — a ReAct
    # question produces more than one (the tool-call message, then the
    # final answer), and both cost real generation time.
    completion_tokens = sum(
        m.response_metadata.get("token_usage", {}).get("completion_tokens", 0)
        for m in result["messages"]
        if m.type == "ai"
    )
    tokens_per_sec = completion_tokens / elapsed if elapsed > 0 else 0.0

    print(
        f"\n[{label}] {elapsed:.1f}s total, {completion_tokens} completion tokens, "
        f"{tokens_per_sec:.1f} tok/s"
    )

    assert elapsed < MAX_SECONDS, (
        f"{label!r} took {elapsed:.1f}s — over the {MAX_SECONDS}s sanity ceiling, "
        f"investigate before assuming it's just normal variance"
    )
