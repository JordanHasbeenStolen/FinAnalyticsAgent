"""Tools the agent can call: execute_python_code and create_chart.

Both follow the same shape: the LLM writes a code string, the tool runs it
against the currently active DataFrame (via `active_table.get_df()`) with
`exec()`, and returns text — either what was printed (execute_python_code)
or the path to a saved PNG (create_chart). Never the raw DataFrame itself.
"""

import contextlib
import io
import uuid
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no display backend needed, figures are only saved to disk
import matplotlib.pyplot as plt
import pandas as pd
from langchain_core.tools import tool

from finanalyticsagent import active_table

MAX_TOOL_OUTPUT_CHARS = 4000
OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(exist_ok=True)

# Matches the app's desert-night theme (see CLAUDE.md "Streamlit UI Design
# Direction"). Transparent figure/axes so the PNG blends into the chat
# bubble instead of showing a stark white box. Single gold hue for bars —
# validated for contrast against the dark surface via the dataviz skill's
# palette validator (this is a single-series magnitude chart, not a
# multi-series categorical one, so one hue is the correct choice, not a
# rainbow per-bar).
CHART_STYLE = {
    "figure.figsize": (6, 4),
    "figure.dpi": 120,
    "figure.facecolor": "none",
    "axes.facecolor": "none",
    "axes.edgecolor": "#8f8570",
    "axes.labelcolor": "#e7dfc6",
    "axes.titlecolor": "#e7dfc6",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.prop_cycle": plt.cycler(color=["#c6963e"]),
    "xtick.color": "#8f8570",
    "ytick.color": "#8f8570",
    "text.color": "#e7dfc6",
    "font.family": "serif",
    "grid.color": "#8f8570",
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
}


@tool
def execute_python_code(code: str) -> str:
    """Run pandas code against the loaded financial DataFrame `df` and return its printed output.

    The DataFrame `df` and the `pd` (pandas) module are already available —
    do not try to import pandas or load/recreate `df` yourself.

    Your code MUST call print(...) on whatever value answers the question.
    Anything not printed is lost — this tool only returns what was printed.

    Print only what you need to answer the question (a single value, a small
    aggregate, a short table) — do not print the entire DataFrame. Output is
    truncated past a length limit, since `df` may be much larger in real use.

    Args:
        code: a snippet of Python/pandas code, e.g.
            "print(df.groupby('Realm')['Net_Income'].sum().idxmax())"

    Returns:
        Everything the code printed to stdout, as a single string (truncated
        if too long, with a note telling you to narrow your query). If the
        code raised an exception instead, returns an "Error: ..." message
        describing what went wrong, so you can fix the code and try again.
    """
    df = active_table.get_df()
    namespace = {"df": df, "pd": pd}
    stdout_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buffer):
            exec(code, namespace)
    except Exception as e:
        return f"Error: {e}"

    output = stdout_buffer.getvalue()
    if not output:
        return "Code ran without errors but printed nothing. Use print() to show a result."

    if len(output) > MAX_TOOL_OUTPUT_CHARS:
        truncated = output[:MAX_TOOL_OUTPUT_CHARS]
        return (
            f"{truncated}\n"
            f"...\n"
            f"[Output truncated at {MAX_TOOL_OUTPUT_CHARS} characters — your code printed too "
            f"much. Narrow your query: filter rows first, aggregate instead of printing raw "
            f"rows, or use .head()/.describe() instead of printing the whole result.]"
        )
    return output


@tool
def create_chart(code: str) -> str:
    """Run matplotlib plotting code against the loaded DataFrame `df` and save it as a PNG.

    The DataFrame `df`, `pd` (pandas), and `plt` (matplotlib.pyplot) are
    already available — do not import them yourself. Your code must
    actually draw something (e.g. plt.bar(...), plt.plot(...), plt.pie(...))
    using data computed from `df`. Do not call plt.show() or plt.savefig()
    yourself — the tool handles saving.

    Args:
        code: a snippet of Python/pandas/matplotlib code that draws a chart,
            e.g. "df.groupby('Realm')['Net_Income'].sum().plot(kind='bar')"

    Returns:
        The file path of the saved PNG (under outputs/), as a string. If the
        code raised an exception, or ran without drawing anything, returns
        an "Error: ..." message describing what went wrong.
    """
    df = active_table.get_df()
    plt.close("all")  # start from a clean figure each time
    namespace = {"df": df, "pd": pd, "plt": plt}
    with plt.rc_context(CHART_STYLE):
        try:
            exec(code, namespace)
        except Exception as e:
            return f"Error: {e}"

        fig = plt.gcf()
        if not fig.get_axes():
            return "Error: no chart was drawn. Call a plotting function like plt.bar(...) or plt.plot(...)."

        for ax in fig.get_axes():
            ax.grid(axis="y", zorder=0)
            ax.set_axisbelow(True)

        filename = OUTPUTS_DIR / f"chart_{uuid.uuid4().hex[:8]}.png"
        fig.savefig(filename, bbox_inches="tight", transparent=True)
        plt.close(fig)
    return str(filename)


def load_table(path: str) -> pd.DataFrame:
    """Load a user-provided table file into a DataFrame, by extension.

    Args:
        path: path to a .csv or .xlsx file.

    Returns:
        The loaded DataFrame.

    Raises:
        ValueError: if the file extension is neither .csv nor .xlsx.
    """
    if path.endswith(".csv"):
        return pd.read_csv(path)
    if path.endswith(".xlsx"):
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type for {path!r}, expected .csv or .xlsx")
