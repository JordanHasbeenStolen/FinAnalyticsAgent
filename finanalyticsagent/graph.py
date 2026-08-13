"""Builds the model and the agent.

`build_agent(tables)` takes a dict argument (not a zero-arg factory) since
the active tables change at runtime — e.g. on file upload — unlike the
static graphs in the official LangGraph templates.
"""

import os
import warnings

import pandas as pd
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from finanalyticsagent import active_table, documents
from finanalyticsagent.prompts import build_documents_section, build_system_prompt
from finanalyticsagent.tools import create_chart, execute_python_code, search_documents

load_dotenv()

# Defaults match this project's own local mlx_lm.server setup — override via
# .env (see .env.example) to point at a different local server, OpenAI, or
# Azure OpenAI (all speak the same Chat Completions wire format ChatOpenAI
# expects). Anthropic is NOT a drop-in base_url swap — it needs
# langchain_anthropic.ChatAnthropic instead, not wired in here.
MODEL_NAME = os.getenv("LLM_MODEL", "Qwen/Qwen3-8B-MLX-4bit")

model = ChatOpenAI(
    model=MODEL_NAME,
    base_url=os.getenv("LLM_BASE_URL", "http://10.195.19.15:8000/v1"),
    api_key=os.getenv("LLM_API_KEY", "dummy"),
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


def build_agent(
    tables: dict[str, pd.DataFrame] | pd.DataFrame,
    document_files: dict[str, str] | None = None,
    selected_document_names: list[str] | None = None,
    persist_documents: bool = True,
):
    """Build a fresh agent bound to the given table(s) and, optionally, documents.

    Args:
        tables: a dict mapping table name to DataFrame — the agent can
            combine several (e.g. via pd.merge) if a question needs it. A
            single DataFrame is also accepted (deprecated), wrapped
            internally as {"df": tables}; kept only so r&d.ipynb's Step 10
            keeps working unmodified.
        document_files: optional mapping of source file name to its full
            extracted text (PDF/DOCX, via documents.load_pdf/load_docx). If
            given, the agent gets a `search_documents` tool backed by an
            in-memory knowledge base built fresh from just these documents —
            this REPLACES the canonical knowledge base for this session
            (uploading your own file means "ask only about this").
        selected_document_names: when `document_files` is not given, which
            of the canonical/persisted documents (documents.CANONICAL_DOCUMENTS)
            to expose — the agent gets `search_documents` restricted to only
            these sources via a metadata filter. Ignored if `document_files`
            is given.
        persist_documents: whether `document_files` (a fresh upload) is
            written to/read from disk (documents.PERSIST_DIR), vs a purely
            in-memory store. Does not affect the `selected_document_names`
            path, which always reads the real persisted store.

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
    tools = [execute_python_code, create_chart]

    if document_files:
        vectorstore = documents.build_knowledge_base(document_files, persist=persist_documents)
        documents.set_vectorstore(vectorstore)
        documents.set_source_filter(None)
        tools.append(search_documents)
        system_prompt += build_documents_section(list(document_files))
    elif selected_document_names:
        vectorstore = documents.ensure_canonical_knowledge_base()
        documents.set_vectorstore(vectorstore)
        documents.set_source_filter(selected_document_names)
        tools.append(search_documents)
        system_prompt += build_documents_section(selected_document_names)

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )
