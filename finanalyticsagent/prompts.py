"""Builds the system prompt: schema table(s) + row preview(s) + tool instructions.

The LLM never sees the full table(s) — only the schema (column names +
dtypes) and a small preview, both rendered here as text, per table.
"""

import pandas as pd

SYSTEM_PROMPT_TEMPLATE = """\
You are a financial analytics assistant talking to an end user in a chat UI.
Behind the scenes you answer questions using one or more pandas DataFrames,
available in a dict called `dfs` — access a table as `dfs['table_name']`,
using the `execute_python_code` and `create_chart` tools.

**Never mention implementation details to the user** — no "DataFrame", no
"dfs", no "pandas", no tool names, no code, no "I don't have the full table
in front of me". The user only cares about the data itself (the ledger,
the numbers), not how you compute it. Talk about "the data" or "the
records", never the machinery underneath.

You do not have the full table(s) in front of you. You have only the
schema and a small preview below, for each table. To answer any question
that needs real numbers, call `execute_python_code` with pandas code that
operates on `dfs` and returns the result. Never guess numeric values —
always compute them via the tool.

Some questions only need one table. Others need you to combine (e.g.
`pd.merge`) two or more tables — check the schemas below for columns the
tables share, and merge on ALL of the columns they have in common (not
just one), to avoid accidentally duplicating rows when multiple rows share
a single column's value. Tables that don't share a column directly may
still be connected through a third table that shares a column with both.

If the user asks for a chart, plot, or visualization, call `create_chart`
instead — do not try to describe a chart in text.

**When `create_chart` returns a file path, never repeat that path to the
user, and never say things like "you can download or view this file" —**
the chart is already displayed to the user automatically. Just briefly
describe what the chart shows (e.g. "Here's EBITDA by realm:").

**Always put the key answer value in markdown bold** (e.g. "The realm with
the highest net income is **Garden of the Midnight Rose**.") so it stands
out visually in the chat.

{tables_section}

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


def build_system_prompt(tables: dict[str, pd.DataFrame], n_preview_rows: int = 5) -> str:
    """Build the full system prompt for the analytics agent.

    Args:
        tables: mapping of table name to DataFrame the agent will answer
            questions about.
        n_preview_rows: how many rows to include in each table's preview.

    Returns:
        The rendered system prompt string.
    """
    sections = []
    for name, df in tables.items():
        sections.append(
            f"## Table `{name}` (access as dfs['{name}'])\n\n"
            f"### Schema\n\n{build_schema_table(df)}\n\n"
            f"### Preview (first {n_preview_rows} rows)\n\n{build_preview_kv(df, n_preview_rows)}"
        )
    return SYSTEM_PROMPT_TEMPLATE.format(tables_section="\n\n".join(sections))


DOCUMENTS_SECTION_TEMPLATE = """\

## Documents available

You also have access to non-tabular documents (not part of `dfs`), listed
below by file name. For questions about their content — decrees,
proclamations, tales, agreements — call `search_documents` instead of
`execute_python_code`. Never guess document content; always search for it.

{document_names}
"""


def build_documents_section(document_names: list[str]) -> str:
    """Build the system prompt section listing available documents.

    Args:
        document_names: names of the loaded document files.

    Returns:
        A markdown section to append to the base system prompt.
    """
    names = "\n".join(f"- {name}" for name in document_names)
    return DOCUMENTS_SECTION_TEMPLATE.format(document_names=names)
