"""Builds the model and the agent.

`build_agent(tables)` takes a dict argument (not a zero-arg factory) since
the active tables change at runtime — e.g. on file upload — unlike the
static graphs in the official LangGraph templates.
"""

import warnings

import pandas as pd
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from finanalyticsagent import active_table
from finanalyticsagent.prompts import build_system_prompt
from finanalyticsagent.tools import create_chart, execute_python_code

MODEL_NAME = "Qwen/Qwen3-8B-MLX-4bit"

model = ChatOpenAI(
    model=MODEL_NAME,
    base_url="http://10.195.19.15:8000/v1",
    api_key="dummy",
    temperature=0,
    max_tokens=8192,
    # 180s: ~2-3x the slowest single-answer latency measured against this
    # server (worst case observed ~70-90s for a heavy reasoning question) —
    # without this, a struggling/crashed Mac hangs the Streamlit app forever
    # instead of surfacing a catchable error.
    request_timeout=180,
)


def answer_was_truncated(result: dict) -> bool:
    """Check whether the agent's final answer was cut off by the token limit.

    Qwen3's hidden `<think>` reasoning shares the same `max_tokens` budget as
    the visible answer, and its length varies wildly between questions
    (observed anywhere from ~60 to 2000+ tokens on near-identical prompts) —
    so it can occasionally consume the whole budget before any visible text
    is produced. Checking `finish_reason == "length"` is the standard way to
    detect this (rather than guessing from answer length/content).

    Args:
        result: the dict returned by agent.invoke(...).

    Returns:
        True if the last AI message was cut off by the token limit.
    """
    last_ai_message = [m for m in result["messages"] if m.type == "ai"][-1]
    return last_ai_message.response_metadata.get("finish_reason") == "length"


def build_agent(tables: dict[str, pd.DataFrame] | pd.DataFrame):
    """Build a fresh agent bound to the given table(s).

    Args:
        tables: a dict mapping table name to DataFrame — the agent can
            combine several (e.g. via pd.merge) if a question needs it. A
            single DataFrame is also accepted (deprecated), wrapped
            internally as {"df": tables}; kept only so r&d.ipynb's Step 10
            keeps working unmodified.

    Returns:
        A compiled agent ready to .invoke({"messages": [...]}).
    """
    if isinstance(tables, pd.DataFrame):
        warnings.warn(
            "build_agent(df) with a single DataFrame is deprecated — pass "
            "a dict of {name: df} instead. Kept only so r&d.ipynb's Step "
            "10 keeps working unmodified.",
            DeprecationWarning,
            stacklevel=2,
        )
        tables = {"df": tables}

    active_table.set_tables(tables)
    system_prompt = build_system_prompt(tables)
    return create_agent(
        model=model,
        tools=[execute_python_code, create_chart],
        system_prompt=system_prompt,
    )
