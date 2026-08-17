# FinAnalyticsAgent
A personal on-prem AI oracle for spreadsheets: summon a djinn from your local LLM through a LangGraph circle, whisper your question to the tabular scroll, and receive the numbers, insights, and charts hidden within


## Overview
 
An agentic replacement for the OpenAI Assistants-style tabular analytics workflow, rebuilt on **LangGraph** with a **locally hosted LLM** (Qwen3-8B on Apple Silicon via `mlx_lm.server`). The agent accepts natural-language questions over spreadsheet data and PDF/DOCX documents (RAG via Chroma), decides which tools to call, and returns answers, insights, or charts, all without sending data to third-party APIs.

![Streamlit chat screenshot](docs/screenshot.png)

## Architecture
 
- **Orchestration:** LangGraph (ReAct pattern), built via `create_agent` from `langchain.agents`
- **LLM:** Qwen3-8B-MLX-4bit (on-prem, OpenAI-compatible endpoint)
- **Data layer:** one or more named pandas DataFrames (`dfs['table_name']`), loaded from CSV/XLSX — the agent can combine several if a question needs it
- **Tooling:** `execute_python_code` for pandas queries; `create_chart` for matplotlib charts — both operate on the `dfs` dict. `search_documents` — real vector search over PDF/DOCX via Chroma + local embeddings (`mlx-omni-server`) — lives in `finanalyticsagent/documents.py`/`tools.py`, wired through `graph.build_agent(tables, document_files, selected_document_names)`; `app.py` offers a canonical demo-document knowledge base (self-seeding, per-document multiselect + metadata filtering) alongside its own-file uploader
- **UI:** Streamlit chat (`app.py`) — desert-night/lamplight theme via `config.toml`, tool-usage transparency toggle (on by default), chart downloads
- **Model backend (planned):** switchable — local LLM (`mlx_lm.server`) is the primary target, with a future option to swap in Azure OpenAI / OpenAI endpoints
## Tools
 
- `execute_python_code(code: str)` — runs LLM-generated pandas code against the loaded table(s) (`dfs['name']`), returns the result
- `create_chart(code: str)` — runs LLM-generated matplotlib code against the loaded table(s), saves the figure to `outputs/*.png`, returns the file path
- `search_documents(query: str)` — vector search over PDF/DOCX documents via Chroma + local embeddings (`mlx-omni-server`, `Qwen3-Embedding-0.6B`), optionally restricted to selected sources via a metadata filter; implemented in `finanalyticsagent/`, exposed via `app.py`'s demo-document multiselect and own-file uploader

## How to Run

```bash
cd FinAnalyticsAgent
source .venv/bin/activate      # or: uv sync
streamlit run app.py
```

Requires a running `mlx_lm.server` endpoint reachable at the address configured
in `finanalyticsagent/graph.py` (or update it to point at your own OpenAI-compatible
local server).

## Roadmap
 
- [x] Repo skeleton and environment setup
- [x] MVP: single agent + one execution tool in Jupyter
- [x] Validate agent against reference questions (from legacy assistant + sample queries) — the generic `execute_python_code` tool + LLM reasoning alone correctly handled all tested questions (single aggregation, per-quarter grouping, growth-over-time, qualitative "why" reasoning, small talk) once `max_tokens` was raised enough for Qwen3's hidden `<think>` reasoning
- [x] Guard `execute_python_code` against printing huge output (e.g. an LLM-generated `print(df)` on a large real-world table) — truncates past a character limit with a clear message instead of flooding the LLM context
- [x] Test user file upload in the notebook — `load_table(path)` generalizes loading beyond one hardcoded file (tested against a second synthetic dataset with an unrelated schema), plus a real click-to-upload flow via `ipywidgets.FileUpload`
- [x] Chart generation tool (`create_chart`) — mirrors `execute_python_code`'s shape (LLM writes plotting code against `df`), saves the figure to `outputs/*.png` (git-ignored, same rationale as `data/`) and returns the path
- [x] Extract code into `.py` modules alongside the notebook — `finanalyticsagent/active_table.py` (current DataFrame), `tools.py`, `prompts.py`, `graph.py` (model+agent construction), `testing.py`. The notebook itself was not touched; it stays as the running R&D log, with a Step 10 proving the modules work standalone
- [x] Streamlit UI (`app.py`) — desert-night/lamplight theme via `config.toml` (no custom CSS), djinn/scroll chat personas, tool-usage transparency (on by default, literal tool names — no roleplay in how the assistant reports its own actions), chart download button, system prompt hardened to never leak implementation details (df/pandas/file paths) to the end user
- [x] `pytest` test suite in `tests/` — pure/deterministic unit tests on `finanalyticsagent/` (schema/preview formatting, `load_table`, the output-truncation guard, the no-chart-drawn error, `active_table`'s `RuntimeError`) plus coarse LLM-in-the-loop regression checks tied to real incidents (small-talk leaks, raw file-path leaks, bold key values, chart transparency); both layers also wired into `r&d.ipynb` as Step 11
- [x] Multi-file support — agent sees several named tables at once (`dfs['name']`), matching how the legacy Assistants API's Code Interpreter worked (see CLAUDE.md for the full phased plan)
  - [x] Prototype in `r&d.ipynb` (new steps only) against the real LLM first
  - [x] Extract into `finanalyticsagent/` (`active_table.py`, `tools.py`, `prompts.py`, `graph.py`), old single-table functions kept as deprecated shims so Step 10 needs no changes
  - [x] Update/add tests
  - [x] Update `app.py` (multi-select demo files + multi-file upload)
- [x] RAG module (Chroma) for non-tabular files (PDF/DOCX) — MVP complete, a minimal live prototype of everything originally planned exists end-to-end
  - [x] Naive keyword-search prototype, no embeddings (`r&d.ipynb` Step 13)
  - [x] First real RAG tests in the notebook — real Chroma + embeddings (`mlx-omni-server`), persistence, live file-upload flow (`r&d.ipynb` Steps 14-17)
  - [x] Extracted into `finanalyticsagent/documents.py` + wired through `tools.py`/`prompts.py`/`graph.py` (`build_agent(tables, document_files, selected_document_names)`) and into `app.py`: a self-seeding canonical demo-document knowledge base (auto-rebuilds if `chroma_db/` is empty) with a per-document multiselect (metadata-filtered search), plus an own-file uploader that replaces the document source for that session (tables and documents each replace independently — uploading one doesn't affect the other)
- [x] RAG quality metrics via RAGAS — `tests/test_rag_metrics.py` + `r&d.ipynb` Step 17 (non-LLM `NonLLMStringSimilarity`; LLM-judge metrics found unreliable on our local model — root cause found and fixed later, see the `enable_thinking=False` entry in `CHANGELOG.md`, 2026-08-14/17)
- [x] LLM-as-judge across three models (Gemma3, Qwen3, Qwen3.5) — `Faithfulness`/`ContextPrecision`/`ContextRecall` via `ragas.metrics.collections`, `r&d.ipynb` Steps 22-23. Gemma3 unusable as a judge (wraps JSON in a markdown fence). Qwen3's hidden `<think>` reasoning was silently eating the token budget on judge calls specifically — fixed via `enable_thinking=False`. Qwen3.5 used as a cross-model judge to check for self-preference bias
- [x] Latency/tokens-per-sec measurement — `tests/test_rag_performance.py` (tabular/document/small-talk questions, generous sanity ceilings, not strict SLAs); not yet surfaced in `app.py`'s own UI
- [ ] Surface latency/tokens-per-sec in `app.py` itself — `mlx_lm.server`'s API only returns token counts (`usage.prompt_tokens`/`completion_tokens`), not a rate, so this needs the same client-side timing the tests already do
- [ ] **Top priority of the open items below:** explore advanced RAG techniques from modern commercial products (reranker, HyDE, better context retrieval) — specifics pending
- [ ] Multi-agent architecture (router + separate document agent) — not planned: single-agent tool-calling already works correctly (`r&d.ipynb` Step 20), a router would only add cost with no measured benefit at the current tool count
- [ ] *(long-term)* Docling for `.docx` parsing (alternative to `python-docx`)
- [ ] *(settled, not revisiting)* Chroma vs Qdrant — staying on Chroma for all foreseeable stages
- [x] Conversation memory, in-session — sliding window (sidebar slider, default 3 previous messages), paired with a `request_timeout` on the model so a slow/struggling backend surfaces a UI error instead of hanging forever
- [ ] *(long-term)* Conversation memory across sessions (persisted across app restarts) — only worth it if the in-session version proves insufficient
- [ ] Model backend switcher — not a UI toggle; `app.py` should read whichever
      backend `.env` already points to and adjust its own text accordingly
      (e.g. swap "nothing leaves this network" for a cloud-appropriate note)
      instead of hardcoding the on-prem claim regardless of backend. Likely
      needs an explicit `LLM_PROVIDER=local|openai|azure` var rather than
      guessing from the URL. Not needed right now
- [x] Surface tool-usage transparency to the end user — done as part of the Streamlit UI above
- [ ] *(lowest priority, exploratory)* Dedicated functions/tools for common
      table operations (e.g. groupby-aggregate, filter, growth-over-time) as
      an alternative to the generic `execute_python_code` tool — only worth
      revisiting if we hit a real question the generic tool can't handle;
      so far it has handled everything we've thrown at it
## Stack
 
- Python 3.13, `uv` for env management
- `langgraph`, `langchain`, `langchain-openai`, `langchain-text-splitters`, `langchain-chroma`, `chromadb`, `pandas`, `matplotlib`, `openpyxl`, `ipywidgets`, `streamlit`, `python-docx`, `pymupdf`, `ragas`, `rapidfuzz`, `python-dotenv`
- Development in WSL2 / VS Code / Jupyter
- On-prem inference: `mlx_lm.server` on Apple Silicon

## Status
 
🚧 Active development. MVP (agent + tools + Streamlit UI) works end-to-end,
backed by a `pytest` test suite, with multi-file support **and RAG** (Chroma
+ real local embeddings, persistence, quality checks via RAGAS) — a live,
tested, end-to-end minimal prototype of the whole original plan now exists.
Next up is exploratory/post-MVP work (see roadmap) — multi-agent, Docling,
latency measurement — none of it blocking.
