"""Coarse LLM-in-the-loop regression checks — non-deterministic (a real model
answers), but each check here guards a specific bug that already happened
once during Streamlit review and was only caught by the user looking at the
screen. Requires a reachable mlx_lm.server (see finanalyticsagent/graph.py
for the endpoint) — these are slower than the pure unit tests, run them on
their own: `pytest tests/test_agent_regressions.py`.
"""

import re
from pathlib import Path

import pandas as pd
from PIL import Image

from finanalyticsagent.graph import build_agent

DEMO_FILE = "bazaar_books/caravan_accounts.csv"


def _ask(agent, question: str) -> dict:
    return agent.invoke({"messages": [{"role": "user", "content": question}]})


def _final_answer(result: dict) -> str:
    return result["messages"][-1].content


def _chart_path(result: dict) -> str | None:
    for message in result["messages"]:
        if message.type == "tool" and message.name == "create_chart":
            if isinstance(message.content, str) and message.content.endswith(".png"):
                return message.content
    return None


def test_small_talk_never_mentions_implementation_details():
    agent = build_agent(pd.read_csv(DEMO_FILE))
    answer = _final_answer(_ask(agent, "hi, what can you do?"))

    lowered = answer.lower()
    assert "dataframe" not in lowered
    assert "pandas" not in lowered
    assert not re.search(r"\bdf\b", lowered)


def test_chart_answer_never_leaks_the_raw_file_path():
    agent = build_agent(pd.read_csv(DEMO_FILE))
    answer = _final_answer(_ask(agent, "Can you plot EBITDA by realm?"))

    assert ".png" not in answer
    assert "outputs" not in answer.lower()
    assert "download" not in answer.lower()


def test_final_answer_bolds_the_key_value():
    agent = build_agent(pd.read_csv(DEMO_FILE))
    answer = _final_answer(_ask(agent, "Which realm had the highest net income?"))

    assert "**" in answer


def test_chart_question_produces_a_real_transparent_png():
    agent = build_agent(pd.read_csv(DEMO_FILE))
    result = _ask(agent, "Can you plot EBITDA by realm?")

    chart_path = _chart_path(result)
    assert chart_path is not None
    assert Path(chart_path).exists()

    image = Image.open(chart_path).convert("RGBA")
    corner_alpha = image.getpixel((0, 0))[3]
    assert corner_alpha == 0
