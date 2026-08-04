"""Unit tests for finanalyticsagent.tools: pure, deterministic, no LLM calls."""

import pandas as pd
import pytest

from finanalyticsagent import active_table
from finanalyticsagent.tools import MAX_TOOL_OUTPUT_CHARS, create_chart, execute_python_code, load_table


def test_load_table_raises_on_unsupported_extension():
    with pytest.raises(ValueError):
        load_table("something.pdf")


def test_execute_python_code_truncates_past_the_limit():
    active_table.set_df(pd.DataFrame({"x": [1]}))
    code = f"print('a' * {MAX_TOOL_OUTPUT_CHARS + 1000})"

    result = execute_python_code.func(code)

    assert len(result) < MAX_TOOL_OUTPUT_CHARS + 1000
    assert "truncated" in result
    assert "Narrow your query" in result


def test_create_chart_errors_when_nothing_is_drawn():
    active_table.set_df(pd.DataFrame({"x": [1]}))

    result = create_chart.func("y = 1")

    assert result == "Error: no chart was drawn. Call a plotting function like plt.bar(...) or plt.plot(...)."


def test_execute_python_code_can_combine_multiple_tables():
    active_table.set_tables(
        {
            "a": pd.DataFrame({"key": [1, 2], "val_a": [10, 20]}),
            "b": pd.DataFrame({"key": [1, 2], "val_b": [100, 200]}),
        }
    )

    result = execute_python_code.func("print(dfs['a'].merge(dfs['b'], on='key')['val_b'].sum())")

    assert result.strip() == "300"
