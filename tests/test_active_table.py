"""Unit tests for finanalyticsagent.active_table: pure, deterministic, no LLM calls."""

import pytest

from finanalyticsagent import active_table


def test_get_df_raises_when_nothing_was_set():
    with pytest.raises(RuntimeError):
        active_table.get_df()
