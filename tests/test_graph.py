"""Unit tests for finanalyticsagent.graph: pure, deterministic, no LLM calls."""

from dataclasses import dataclass, field

from finanalyticsagent.graph import answer_was_truncated


@dataclass
class FakeMessage:
    type: str
    response_metadata: dict = field(default_factory=dict)


def test_detects_a_truncated_answer():
    result = {"messages": [FakeMessage(type="ai", response_metadata={"finish_reason": "length"})]}
    assert answer_was_truncated(result) is True


def test_does_not_flag_a_normal_answer():
    result = {"messages": [FakeMessage(type="ai", response_metadata={"finish_reason": "stop"})]}
    assert answer_was_truncated(result) is False
