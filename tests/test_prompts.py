"""Unit tests for finanalyticsagent.prompts: pure, deterministic, no LLM calls."""

import pandas as pd

from finanalyticsagent.prompts import build_preview_kv, build_schema_table, build_system_prompt


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({"Name": ["Alice", "Bob"], "Score": [10, 20]})


def test_build_schema_table_renders_columns_and_dtypes():
    expected = "| column | dtype |\n|---|---|\n| Name | str |\n| Score | int64 |"
    assert build_schema_table(_sample_df()) == expected


def test_build_preview_kv_renders_rows_as_kv_blocks():
    expected = "Name: Alice\nScore: 10\n---\nName: Bob\nScore: 20"
    assert build_preview_kv(_sample_df(), n_rows=2) == expected


def test_build_system_prompt_renders_one_section_per_table():
    tables = {
        "people": _sample_df(),
        "other": pd.DataFrame({"Z": [1, 2]}),
    }

    prompt = build_system_prompt(tables, n_preview_rows=2)

    assert "dfs['people']" in prompt
    assert "dfs['other']" in prompt
    assert "Name: Alice" in prompt
    assert prompt.index("dfs['people']") < prompt.index("dfs['other']")
