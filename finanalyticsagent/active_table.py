"""Holds the table(s) currently active for the agent.

Not a LangGraph state schema — the agent is built with `create_agent`,
which manages its own internal message state. This is just a get/set pair
so `tools.py` and `prompts.py` can both see whichever tables are currently
loaded, since a plain module-level variable in one file doesn't work once
the code is split across files.
"""

import warnings

import pandas as pd

_active_tables: dict[str, pd.DataFrame] | None = None


def set_tables(tables: dict[str, pd.DataFrame]) -> None:
    """Set the tables that tools and prompts should operate on.

    Args:
        tables: mapping of table name to DataFrame. The agent can combine
            more than one (e.g. via pd.merge) if a question needs it.
    """
    global _active_tables
    _active_tables = tables


def get_tables() -> dict[str, pd.DataFrame]:
    """Get the currently active tables.

    Returns:
        The dict set by the most recent call to set_tables.

    Raises:
        RuntimeError: if no tables have been set yet.
    """
    if _active_tables is None:
        raise RuntimeError("No tables loaded yet — call set_tables(...) first.")
    return _active_tables


@warnings.deprecated(
    "Use set_tables({'df': df}) instead — kept only so r&d.ipynb's Step 10 keeps working unmodified."
)
def set_df(df: pd.DataFrame) -> None:
    """Set a single DataFrame as the active table, under the name 'df'.

    Args:
        df: the DataFrame to make active.
    """
    set_tables({"df": df})


@warnings.deprecated(
    "Use get_tables() instead — kept only so r&d.ipynb's Step 10 keeps working unmodified."
)
def get_df() -> pd.DataFrame:
    """Get the DataFrame set by the most recent call to set_df.

    Returns:
        The DataFrame stored under the name 'df'.

    Raises:
        RuntimeError: if no tables have been set yet.
    """
    return get_tables()["df"]
