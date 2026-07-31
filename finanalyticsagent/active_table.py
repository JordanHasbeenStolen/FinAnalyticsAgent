"""Holds the DataFrame currently active for the agent.

Not a LangGraph state schema — the agent is built with `create_agent`,
which manages its own internal message state. This is just a get/set pair
so `tools.py` and
`prompts.py` can both see whichever table is currently loaded, since a
plain module-level variable in one file (as in the notebook) doesn't work
once the code is split across files.
"""

import pandas as pd

_active_df: pd.DataFrame | None = None


def set_df(df: pd.DataFrame) -> None:
    """Set the DataFrame that tools and prompts should operate on.

    Args:
        df: the DataFrame to make active.
    """
    global _active_df
    _active_df = df


def get_df() -> pd.DataFrame:
    """Get the currently active DataFrame.

    Returns:
        The DataFrame set by the most recent call to set_df.

    Raises:
        RuntimeError: if no DataFrame has been set yet.
    """
    if _active_df is None:
        raise RuntimeError("No DataFrame loaded yet — call set_df(df) first.")
    return _active_df
