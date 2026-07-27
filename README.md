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
- [ ] MVP: single agent + one execution tool in Jupyter
- [ ] Chart generation tool
- [ ] Streamlit UI
- [ ] Multi-file support (upload arbitrary tables)
- [ ] Conversation memory across sessions
- [ ] Optional: switch backend to DeepSeek or other local models
## Stack
 
- Python 3.12, `uv` for env management
- `langgraph`, `langchain`, `langchain-openai`, `pandas`, `matplotlib`
- Development in WSL2 / VS Code / Jupyter
- On-prem inference: `mlx_lm.server` on Apple Silicon
## Status
 
🚧 Early development. Prototype in Jupyter, refactoring toward a reusable package.