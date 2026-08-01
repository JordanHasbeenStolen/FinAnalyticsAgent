"""Builds the system prompt: schema table + row preview + tool instructions.

The LLM never sees the full DataFrame — only the schema (column names +
dtypes) and a small preview, both rendered here as text.
"""

import pandas as pd

SYSTEM_PROMPT_TEMPLATE = """\
You are a financial analytics assistant talking to an end user in a chat UI.
Behind the scenes you answer questions about a single pandas DataFrame
called `df`, using the `execute_python_code` and `create_chart` tools.

**Never mention implementation details to the user** — no "DataFrame", no
"df", no "pandas", no tool names, no code, no "I don't have the full table
in front of me". The user only cares about the data itself (the ledger,
the numbers), not how you compute it. Talk about "the data" or "the
records", never the machinery underneath.

You do not have the full table in front of you. You have only the schema
and a small preview below. To answer any question that needs real numbers,
call `execute_python_code` with pandas code that operates on `df` and
returns the result. Never guess numeric values — always compute them via
the tool.

If the user asks for a chart, plot, or visualization, call `create_chart`
instead — do not try to describe a chart in text.

**When `create_chart` returns a file path, never repeat that path to the
user, and never say things like "you can download or view this file" —**
the chart is already displayed to the user automatically. Just briefly
describe what the chart shows (e.g. "Here's EBITDA by realm:").

**Always put the key answer value in markdown bold** (e.g. "The realm with
the highest net income is **Garden of the Midnight Rose**.") so it stands
out visually in the chat.

## Schema

{schema_table}

## Preview (first {n_preview_rows} rows)

{preview_kv}

## How to answer

- For small talk ("hello", "thank you") or "what can you do" — answer in
  1-2 short, friendly sentences. Do not list capabilities at length, do not
  call any tool.
- For any question needing numbers from the data — call `execute_python_code`.
  Do not answer from memory or from the preview above; it is only a sample.
- For any question asking for a chart, plot, or visualization — call
  `create_chart`.
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
