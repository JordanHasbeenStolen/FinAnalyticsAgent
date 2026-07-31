"""Builds the system prompt: schema table + row preview + tool instructions.

The LLM never sees the full DataFrame — only the schema (column names +
dtypes) and a small preview, both rendered here as text.
"""

import pandas as pd

SYSTEM_PROMPT_TEMPLATE = """\
You are a financial analytics assistant. You answer questions about a single
pandas DataFrame called `df`, which is already loaded in your execution
environment — you never need to load or recreate it.

You do not have the full table in front of you. You have only the schema
and a small preview below. To answer any question that needs real numbers,
you must call the `execute_python_code` tool with pandas code that operates
on `df` and returns the result. Never guess numeric values — always compute
them via the tool.

If the user asks for a chart, plot, or visualization, use the `create_chart`
tool instead — it runs matplotlib code against `df` and returns the path to
a saved PNG. Do not try to describe a chart in text; use the tool.

## Schema

{schema_table}

## Preview (first {n_preview_rows} rows)

{preview_kv}

## How to answer

- For small talk ("hello", "thank you") — respond directly, do not call the tool.
- For any question needing numbers from the data — write pandas code against
  `df` and call `execute_python_code`. Do not answer from memory or from the
  preview above; the preview is only a sample, not the full data.
- For any question asking for a chart, plot, or visualization — call
  `create_chart` instead.
"""


def build_schema_table(df: pd.DataFrame) -> str:
    """Render column names + dtypes as a markdown table.

    Args:
        df: the DataFrame to describe.

    Returns:
        A markdown table string, one row per column: "column | dtype".
    """
    lines = ["| column | dtype |", "|---|---|"]
    for column_name, dtype in df.dtypes.items():
        lines.append(f"| {column_name} | {dtype} |")
    return "\n".join(lines)


def build_preview_kv(df: pd.DataFrame, n_rows: int = 5) -> str:
    """Render the first n_rows of a DataFrame as markdown-KV blocks.

    Each row becomes a block of "column: value" lines separated by "---".
    Chosen over a markdown table for better small-model comprehension.

    Args:
        df: the DataFrame to preview.
        n_rows: how many rows from the top to include.

    Returns:
        A markdown-KV formatted string.
    """
    blocks = []
    for _, row in df.head(n_rows).iterrows():
        lines = [f"{column_name}: {value}" for column_name, value in row.items()]
        blocks.append("\n".join(lines))
    return "\n---\n".join(blocks)


def build_system_prompt(df: pd.DataFrame, n_preview_rows: int = 5) -> str:
    """Build the full system prompt for the analytics agent.

    Args:
        df: the DataFrame the agent will answer questions about.
        n_preview_rows: how many rows to include in the preview section.

    Returns:
        The rendered system prompt string.
    """
    return SYSTEM_PROMPT_TEMPLATE.format(
        schema_table=build_schema_table(df),
        n_preview_rows=n_preview_rows,
        preview_kv=build_preview_kv(df, n_preview_rows),
    )
