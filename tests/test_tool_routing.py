"""Tool-selection regression checks — non-deterministic (a real model
answers), requires reachable mlx_lm.server + mlx-omni-server. Slower than
the pure unit tests, run on its own: `pytest tests/test_tool_routing.py`.

Builds the agent via `finanalyticsagent.graph.build_agent(tables,
document_files)` with `persist_documents=False` (in-memory knowledge base,
never touches the shared `chroma_db/` on disk) — same pattern as
`test_rag_metrics.py`.

`conftest.py`'s `reset_active_table` autouse fixture wipes
`active_table._active_tables` before/after every test in `tests/` — correct
for tests that build a fresh agent per test, but it also wipes the state
set by this file's module-scoped `routing_agent` fixture (built once, to
avoid re-embedding all 4 documents for every question). Each test below
therefore also depends on `restore_tables`, a function-scoped fixture that
re-sets the tables right before the test body runs, after the autouse
fixture's wipe — confirmed via a live pytest run that omitting it causes
every tabular-tool test to fail with "No tables loaded yet" even though
`build_agent` set them correctly at fixture-build time.

Checks are deliberately soft (`in`/`not in`, not exact set equality) — the
LLM's exact tool-call sequence isn't fully deterministic even at
temperature=0 (see CLAUDE.md), so asserting the full set would make this
test flaky for reasons unrelated to real routing regressions. What matters
is: did the right tool get used at all, and did the agent avoid the wrong
one on the ambiguous case (tabular-priority check, added 2026-08-12 based
on a live baseline run in `r&d.ipynb` Step 20 that already showed this
behavior without any prompt change — this test locks that behavior in so a
future prompt edit can't silently regress it).
"""

import pandas as pd
import pytest

from finanalyticsagent import active_table, documents
from finanalyticsagent.graph import build_agent


@pytest.fixture(scope="module")
def dfs():
    return {
        "caravan_accounts": pd.read_csv("bazaar_books/caravan_accounts.csv"),
        "guild_ledger": pd.read_csv("bazaar_books/guild_ledger.csv"),
        "realm_metadata": pd.read_csv("bazaar_books/realm_metadata.csv"),
    }


@pytest.fixture(scope="module")
def routing_agent(dfs):
    document_files = {
        "zau_al_makan_decree.docx": documents.load_docx("bazaar_books/zau_al_makan_decree.docx"),
        "hammam_keeper_proclamation.pdf": documents.load_pdf("bazaar_books/hammam_keeper_proclamation.pdf"),
        "taj_al_muluk_bazaar.docx": documents.load_docx("bazaar_books/taj_al_muluk_bazaar.docx"),
        "aziz_reckoning.pdf": documents.load_pdf("bazaar_books/aziz_reckoning.pdf"),
    }

    return build_agent(dfs, document_files, persist_documents=False)


@pytest.fixture
def restore_tables(dfs):
    """Undo conftest.py's per-test active_table wipe for this module-scoped agent."""
    active_table.set_tables(dfs)


def _tool_calls(result: dict) -> set[str]:
    return {call["name"] for m in result["messages"] if m.type == "ai" for call in m.tool_calls}


def test_tabular_question_uses_execute_python_code(routing_agent, restore_tables):
    result = routing_agent.invoke(
        {"messages": [{"role": "user", "content": "Which realm had the highest net income?"}]}
    )
    assert "execute_python_code" in _tool_calls(result)


def test_document_question_uses_search_documents(routing_agent, restore_tables):
    result = routing_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "In Taj al-Muluk's story, what was the price of the finest bolt of dibaj?",
                }
            ]
        }
    )
    assert "search_documents" in _tool_calls(result)


def test_mixed_question_uses_both_tools(routing_agent, restore_tables):
    result = routing_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "What was the total value of Aziz's day's trade according to his "
                        "reckoning, and which realm's net income is closest to that amount?"
                    ),
                }
            ]
        }
    )
    called = _tool_calls(result)
    assert "search_documents" in called
    assert "execute_python_code" in called


def test_ambiguous_question_prefers_tabular_over_rag(routing_agent, restore_tables):
    result = routing_agent.invoke(
        {"messages": [{"role": "user", "content": "What was the total trade value?"}]}
    )
    assert "search_documents" not in _tool_calls(result)
