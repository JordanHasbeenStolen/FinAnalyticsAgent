"""Builds the model and the agent.

`build_agent(df)` takes a DataFrame argument (not a zero-arg factory) since
the active table changes at runtime — e.g. on file upload — unlike the
static graphs in the official LangGraph templates.
"""

import pandas as pd
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from finanalyticsagent import active_table
from finanalyticsagent.prompts import build_system_prompt
from finanalyticsagent.tools import create_chart, execute_python_code

model = ChatOpenAI(
    model="Qwen/Qwen3-8B-MLX-4bit",
    base_url="http://10.195.19.15:8000/v1",
    api_key="dummy",
    temperature=0,
    max_tokens=8192,
)


def build_agent(df: pd.DataFrame):
    """Build a fresh agent bound to the given DataFrame.

    Args:
        df: the DataFrame the agent should answer questions about. Becomes
            the active table for execute_python_code and create_chart.

    Returns:
        A compiled agent ready to .invoke({"messages": [...]}).
    """
    active_table.set_df(df)
    system_prompt = build_system_prompt(df)
    return create_agent(
        model=model,
        tools=[execute_python_code, create_chart],
        system_prompt=system_prompt,
    )
