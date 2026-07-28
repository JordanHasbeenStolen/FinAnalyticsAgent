# CLAUDE.md

Context file for Claude Code. Read this file at the start of every session in this project.

**Note:** There is also a `CLAUDE.local.md` (git-ignored) with additional personal context and communication preferences. Read it if it exists.

---

## Project Overview

**FinAnalyticsAgent** — a personal on-prem AI oracle for spreadsheets. A LangGraph agent bound to a locally-hosted Qwen3-8B LLM that reads tabular data (CSV/XLSX) and answers natural-language questions: aggregations, insights, charts.

**Why on-prem:** no data leaves the local network. Important for privacy-sensitive tabular data.

---

## Tech Stack

- **Language:** Python 3.13.5
- **Package manager:** `uv`
- **Environment:** WSL2 Ubuntu, VS Code + Jupyter
- **LLM:** `Qwen/Qwen3-8B-MLX-4bit` via `mlx_lm.server` on a separate Apple Silicon Mac in the local network. Endpoint URL is stored in `.env`, not committed.
- **Orchestration:** LangGraph 1.2.x
- **LangChain:** 1.3.x (v1.0 released April 2026 with breaking changes — do not rely on pre-1.0 patterns)
- **Data:** pandas, matplotlib, openpyxl
- **UI (planned):** Streamlit

Dependencies are in `pyproject.toml`, locked in `uv.lock`. Add new packages via `uv add <package>`.

---

## Architecture

**ReAct pattern** on LangGraph. Fast path: use `create_react_agent` from `langgraph.prebuilt`.

### Tools
- `execute_python_code(code: str)` — runs LLM-generated pandas code against a pre-loaded DataFrame, returns the result
- `create_chart(code: str)` — matplotlib chart generation, saves PNG to `outputs/`, returns file path *(phase 2)*
- Future: `read_new_table(path)` for arbitrary table uploads

### State
`TypedDict` with `messages: Annotated[list[AnyMessage], operator.add]`.

### Memory
`MemorySaver` for in-session continuity. `thread_id` = session identifier.

### Data flow
The full DataFrame is **never** put into the LLM prompt. Only:
- Schema (column names + dtypes) in the system prompt
- First 3–5 rows as preview
- All actual queries go through tools

---

## Synthetic Data Setting: Sharrkan & Zau al-Makan

Real financial data lives in `data/` (git-ignored, never committed). For anything that needs to go into git — demos, tests, notebook examples shown in a portfolio context — we use a synthetic dataset styled after **One Thousand and One Nights**, specifically the tale of **King Omar bin al-Nu'uman and his sons Sharrkan and Zau al-Makan**.

- **File:** `bazaar_books/caravan_accounts.csv` (tracked in git, not ignored)
- **Columns:** `Realm, Guild_Name, Year, Quarter, Operating_Income, EBITDA, Tax, Net_Income, GOGS` — same shape as the real `new_fin.csv`, values fully synthetic (randomly generated, not derived from real data)
- **Realms:** invented fantastical lands (e.g. "Oasis of Whispering Sands", "Peak of the Sleeping Djinn") — deliberately not real countries
- **Guilds:** in-universe trading houses/guilds (e.g. "Djinn-Forged Ironworks", "Forty Thieves Foundry")
- **Years:** 717–718 — the historical Umayyad siege of Constantinople, the event the Sharrkan/Zau al-Makan story is loosely modeled on

**Why this story specifically:** the tale has genuine treasury/business texture — e.g. the bath-attendant (hammam keeper) who helps Zau al-Makan also runs his own trade — which maps naturally onto a financial-ledger dataset. Future synthetic data or flavor text for this project can keep drawing on this same story for consistency.

---

## Code Style

### Python
- Python 3.13 features are OK (union types with `|`, structural pattern matching if truly clearer).
- **Type hints** on public functions and tool signatures.
- **Docstrings** on every tool and non-trivial function. Tool docstrings go into the LLM's prompt — write them thoroughly: behavior, args, returns, when to use.
- Prefer f-strings over `.format()` or `%`.
- `from module import name` style is preferred for readability.
- Group imports: stdlib → third-party → local. Blank line between groups.

### LangGraph project layout
Extract from notebook to modules once code stabilizes:
- `state.py` — state classes
- `tools.py` — tool functions
- `nodes.py` — node implementations
- `graph.py` — `build_agent()` returns a compiled graph
- `prompts.py` — system prompts as string constants

### Notebooks
- Names: `NN_description.ipynb` (leading number for order).
- Use for exploration; move working code to `.py` modules.

---

## Git Workflow

- Work on `main` branch. Feature branches only for experimental changes we might discard.
- **Commit early, commit often.** Small commits, clear messages. Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- **Never commit:** `.venv/`, `.env`, raw data files, notebook checkpoints, IDE configs. All in `.gitignore`.
- **Author identity:** locally configured for this repo (not `--global`).
- **Remote:** HTTPS with a fine-grained PAT.
- Before push, run `git status` and `git log origin/main..HEAD --stat` if anything is uncertain.

---

## Common Commands

### Environment
```bash
source .venv/bin/activate
uv add <package>          # install + track in pyproject.toml
uv sync                   # reinstall from lockfile
```

### Jupyter fallback (when VS Code Jupyter misbehaves)
```bash
jupyter lab --no-browser --port 8888
```

### Git
```bash
git status
git log --oneline -n 10
git add <specific files>
git commit -m "type: short imperative summary"
git push
```

---

## Current Status & Next Steps

### Done
- [x] Repo initialized, project structure in place
- [x] Dependencies installed via uv
- [x] Stack check passes — LLM responds via LangChain

### Next up
1. Load `new_fin.csv` into pandas, inspect schema
2. Design the schema-and-preview system prompt
3. Build `execute_python_code` tool
4. Wire into ReAct agent via `create_react_agent`
5. First end-to-end query: "Which country had the highest net income in 2023?"
6. Iterate on sample queries
7. Add `create_chart` tool (phase 2)
8. Extract logic from notebook to `.py` modules
9. Streamlit UI (phase 3)

---

## Rules for Claude Code

- **Verify current library APIs.** LangChain and LangGraph both hit v1.0 in April 2026 with breaking changes. Don't rely on 2024 documentation patterns.
- **The model is Qwen3-8B, not GPT-4.** Prompts must be explicit; tool docstrings thorough; small models need more guidance.
- **Ask before destructive actions:** rewriting git history, `git push --force`, deleting files, restructuring project layout.
- **Announce non-trivial actions before doing them.** Especially git operations, file moves, dependency installs.
- **Never hardcode credentials.** All secrets in `.env`.
- **Never commit real data.** Files in `data/*.csv` and `data/*.xlsx` are git-ignored on purpose.
- **Prefer the fastest path to a working prototype.** This is a personal MVP, not a production system. Don't propose custom implementations when a prebuilt one works. Don't refactor unless asked.