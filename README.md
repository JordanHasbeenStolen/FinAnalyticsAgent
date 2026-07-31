# FinAnalyticsAgent
A personal on-prem AI oracle for spreadsheets: summon a djinn from your local LLM through a LangGraph circle, whisper your question to the tabular scroll, and receive the numbers, insights, and charts hidden within


## Overview
 
An agentic replacement for the OpenAI Assistants-style tabular analytics workflow, rebuilt on **LangGraph** with a **locally hosted LLM** (Qwen3-8B on Apple Silicon via `mlx_lm.server`). The agent accepts natural-language questions over spreadsheet data, decides which tools to call, and returns answers, insights, or charts — all without sending data to third-party APIs.
 
## Architecture
 
- **Orchestration:** LangGraph (ReAct pattern, custom agent graph)
- **LLM:** Qwen3-8B-MLX-4bit (on-prem, OpenAI-compatible endpoint)
- **Data layer:** pandas DataFrame loaded from CSV/XLSX
- **Tooling:** `execute_python_code` for pandas queries; `create_chart` for matplotlib charts
- **UI (planned):** Streamlit for interactive chat
- **Model backend (planned):** switchable — local LLM (`mlx_lm.server`) is the primary target, with a future option to swap in Azure OpenAI / OpenAI endpoints
## Tools
 
- `execute_python_code(code: str)` — runs LLM-generated pandas code against the loaded DataFrame, returns the result
- `create_chart(code: str)` — runs LLM-generated matplotlib code against the loaded DataFrame, saves the figure to `outputs/*.png`, returns the file path
## Roadmap
 
- [x] Repo skeleton and environment setup
- [x] MVP: single agent + one execution tool in Jupyter
- [x] Validate agent against reference questions (from legacy assistant + sample queries) — the generic `execute_python_code` tool + LLM reasoning alone correctly handled all tested questions (single aggregation, per-quarter grouping, growth-over-time, qualitative "why" reasoning, small talk) once `max_tokens` was raised enough for Qwen3's hidden `<think>` reasoning
- [x] Guard `execute_python_code` against printing huge output (e.g. an LLM-generated `print(df)` on a large real-world table) — truncates past a character limit with a clear message instead of flooding the LLM context
- [x] Test user file upload in the notebook — `load_table(path)` generalizes loading beyond one hardcoded file (tested against a second synthetic dataset with an unrelated schema), plus a real click-to-upload flow via `ipywidgets.FileUpload`
- [x] Chart generation tool (`create_chart`) — mirrors `execute_python_code`'s shape (LLM writes plotting code against `df`), saves the figure to `outputs/*.png` (git-ignored, same rationale as `data/`) and returns the path
- [x] Extract code into `.py` modules alongside the notebook — `finanalyticsagent/active_table.py` (current DataFrame), `tools.py`, `prompts.py`, `graph.py` (model+agent construction), `testing.py`. The notebook itself was not touched; it stays as the running R&D log, with a Step 10 proving the modules work standalone
- [ ] Streamlit UI — visual design direction decided (desert-night/lamplight palette, `Amiri`/`Alegreya`/`JetBrains Mono` type, djinn/scroll chat personas, all via Streamlit's native `config.toml` theming — no custom CSS), see `CLAUDE.md` for the full token spec. Not built yet.
- [ ] `pytest` test suite in `tests/` — starting with the pure, deterministic functions in `finanalyticsagent/` (no formal tests exist yet; the notebook's manual check cells stay in the notebook, per its own "never trimmed" rule)
- [ ] Multi-file support (upload arbitrary tables)
- [ ] RAG module (Chroma) for non-tabular files (PDF/DOC)
  - [ ] File-type router: tabular files → pandas tools, PDF/DOC → RAG
  - [ ] Router decides by file content and/or extension
  - [ ] Graceful degradation: if the RAG module/embedding endpoint is unavailable, tell the user explicitly ("you uploaded a PDF, RAG is needed, but the module is unavailable") instead of failing silently — important for demos
  - [ ] Embedding model currently only runs locally via Ollama; plan needed for running embedding models within the existing Mac/MLX setup instead
- [ ] Conversation memory across sessions
- [ ] Model backend switcher — local LLM stays the primary target, but add the
      ability to swap in Azure OpenAI / OpenAI endpoints (or other local
      models like DeepSeek) without rewriting the agent code
- [ ] Surface tool-usage transparency to the end user (in the notebook's test
      loop we already log "used tool" vs "answered directly" per question —
      carry this into the real UI so users can tell verified-via-code answers
      apart from raw LLM reasoning)
- [ ] *(lowest priority, exploratory)* Dedicated functions/tools for common
      table operations (e.g. groupby-aggregate, filter, growth-over-time) as
      an alternative to the generic `execute_python_code` tool — only worth
      revisiting if we hit a real question the generic tool can't handle;
      so far it has handled everything we've thrown at it
## Stack
 
- Python 3.13, `uv` for env management
- `langgraph`, `langchain`, `langchain-openai`, `pandas`, `matplotlib`, `ipywidgets`
- Development in WSL2 / VS Code / Jupyter
- On-prem inference: `mlx_lm.server` on Apple Silicon
## Status
 
🚧 Early development. Prototype in Jupyter, refactoring toward a reusable package.
