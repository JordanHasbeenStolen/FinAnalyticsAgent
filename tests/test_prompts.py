"""Unit tests for finanalyticsagent.prompts: pure, deterministic, no LLM calls."""

import pandas as pd

from finanalyticsagent.prompts import build_preview_kv, build_schema_table


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({"Name": ["Alice", "Bob"], "Score": [10, 20]})


def test_build_schema_table_renders_columns_and_dtypes():
    expected = "| column | dtype |\n|---|---|\n| Name | str |\n| Score | int64 |"
    assert build_schema_table(_sample_df()) == expected


def test_build_preview_kv_renders_rows_as_kv_blocks():
    expected = "Name: Alice\nScore: 10\n---\nName: Bob\nScore: 20"
    assert build_preview_kv(_sample_df(), n_rows=2) == expected
