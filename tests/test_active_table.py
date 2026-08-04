"""Unit tests for finanalyticsagent.active_table: pure, deterministic, no LLM calls."""

import pandas as pd
import pytest

from finanalyticsagent import active_table


def test_get_tables_raises_when_nothing_was_set():
    with pytest.raises(RuntimeError):
        active_table.get_tables()


def test_set_tables_then_get_tables_returns_the_same_dict():
    tables = {"a": pd.DataFrame({"x": [1]}), "b": pd.DataFrame({"y": [2]})}

    active_table.set_tables(tables)

    # `is`, not `==` — comparing DataFrames with `==` raises (ambiguous
    # truth value), and set_tables stores the dict reference as-is anyway.
    assert active_table.get_tables() is tables


def test_get_df_raises_when_nothing_was_set():
    with pytest.raises(RuntimeError):
        active_table.get_df()


def test_set_df_then_get_df_round_trips_under_the_name_df():
    df = pd.DataFrame({"x": [1]})

    active_table.set_df(df)

    assert active_table.get_df() is df
