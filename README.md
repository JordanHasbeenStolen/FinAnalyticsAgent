# FinAnalyticsAgent
A personal on-prem AI oracle for spreadsheets: summon a djinn from your local LLM through a LangGraph circle, whisper your question to the tabular scroll, and receive the numbers, insights, and charts hidden within


## Overview
 
An agentic replacement for the OpenAI Assistants-style tabular analytics workflow, rebuilt on **LangGraph** with a **locally hosted LLM** (Qwen3-8B on Apple Silicon via `mlx_lm.server`). The agent accepts natural-language questions over spreadsheet data, decides which tools to call, and returns answers, insights, or charts — all without sending data to third-party APIs.
 
## Architecture
 
- **Orchestration:** LangGraph (ReAct pattern, custom agent graph)
- **LLM:** Qwen3-8B-MLX-4bit (on-prem, OpenAI-compatible endpoint)
- **Data layer:** pandas DataFrame loaded from CSV/XLSX
- **Tooling:** `execute_python_code` for pandas queries and matplotlib charts
- **UI (planned):** Streamlit for interactive chat
## Tools
 
- `execute_python_code(code: str)` — runs LLM-generated pandas code against the loaded DataFrame, returns the result
- `create_chart(code: str)` *(planned)* — matplotlib chart generation, saves to disk, returns file path
## Roadmap
 
- [x] Repo skeleton and environment setup
- [x] MVP: single agent + one execution tool in Jupyter
- [ ] Validate agent against reference questions (from legacy assistant + sample queries)
  - [ ] First pass: cover reference questions with the generic `execute_python_code` tool + LLM reasoning alone
  - [ ] Then: incrementally add dedicated tools for common table operations (e.g. filtering by column, groupby aggregation, growth-over-time) where the generic tool proves insufficient
  - [ ] Agent should be transparent about *how* it answered — whether it used a specific tool or answered directly from reasoning
  - [ ] Test user file upload in the notebook (near-term, before moving to modules)
- [ ] Chart generation tool (`create_chart`) — start small, expand incrementally
- [ ] Extract notebook code into `.py` modules (`state.py`, `tools.py`, `prompts.py`, `graph.py` — exporting a `graph` object per LangGraph convention, no separate `nodes.py` or `build_agent()` factory)
- [ ] Streamlit UI
- [ ] Multi-file support (upload arbitrary tables)
- [ ] RAG module (Chroma) for non-tabular files (PDF/DOC)
  - [ ] File-type router: tabular files → pandas tools, PDF/DOC → RAG
  - [ ] Router decides by file content and/or extension
  - [ ] Graceful degradation: if the RAG module/embedding endpoint is unavailable, tell the user explicitly ("you uploaded a PDF, RAG is needed, but the module is unavailable") instead of failing silently — important for demos
  - [ ] Embedding model currently only runs locally via Ollama; plan needed for running embedding models within the existing Mac/MLX setup instead
- [ ] Conversation memory across sessions
- [ ] Optional: switch backend to DeepSeek or other local models
## Stack
 
- Python 3.12, `uv` for env management
- `langgraph`, `langchain`, `langchain-openai`, `pandas`, `matplotlib`
- Development in WSL2 / VS Code / Jupyter
- On-prem inference: `mlx_lm.server` on Apple Silicon
## Status
 
🚧 Early development. Prototype in Jupyter, refactoring toward a reusable package.
