"""Small helper for manually testing an agent and seeing what it did.

Not a tool, not part of the agent itself — just a convenience for
development: run one question, print which tool (if any) was called and
with what code, and the final answer.
"""


def run_question(agent, question: str) -> None:
    """Run one question through the agent and print a compact transparency report.

    Args:
        agent: the compiled agent to invoke.
        question: the natural-language question to ask.
    """
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    print(f"Q: {question}")

    tool_calls_made = [
        (call["name"], call["args"]["code"])
        for message in result["messages"]
        if message.type == "ai"
        for call in message.tool_calls
    ]
    if tool_calls_made:
        for tool_name, code in tool_calls_made:
            print(f"Used {tool_name} with:")
            print(f"  {code}")
    else:
        print("Answered directly, no tool call.")

    final_answer = result["messages"][-1].content
    print(f"A: {final_answer}")
    print("-" * 80)
