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
  Local LLM is the primary target long-term; a future model-backend switcher
  (to swap in Azure OpenAI / OpenAI endpoints) is planned — see roadmap.
- **Orchestration:** LangGraph 1.2.x
- **LangChain:** 1.3.x (v1.0 released April 2026 with breaking changes — do not rely on pre-1.0 patterns)
- **Data:** pandas, matplotlib, openpyxl, ipywidgets (for the notebook's file-upload widget)
- **UI (planned):** Streamlit

Dependencies are in `pyproject.toml`, locked in `uv.lock`. Add new packages via `uv add <package>`.

---

## Architecture

**ReAct pattern**, built with `create_agent` from `langchain.agents` (verified 2026-07-28:
`create_react_agent` from `langgraph.prebuilt` is now deprecated in favor of this).

### Tools
- `execute_python_code(code: str)` — runs LLM-generated pandas code against a pre-loaded DataFrame, returns the result. Truncates output past `MAX_TOOL_OUTPUT_CHARS` with a clear message instead of flooding the LLM context.
- `create_chart(code: str)` — matplotlib chart generation, saves PNG to `outputs/` (git-ignored, same rationale as `data/`), returns file path
- `load_table(path)` — loads a `.csv`/`.xlsx` by extension; this is the built version of what the roadmap used to call `read_new_table(path)`. Combined with `ipywidgets.FileUpload` in the notebook for a real click-to-upload flow.

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

- **Files (both tracked in git, not ignored):**
  - `bazaar_books/caravan_accounts.csv` — columns `Realm, Guild_Name, Year, Quarter, Operating_Income, EBITDA, Tax, Net_Income, GOGS`, same shape as the real `new_fin.csv`, values fully synthetic (randomly generated, not derived from real data)
  - `bazaar_books/guild_ledger.csv` — a second synthetic dataset with a deliberately different, non-financial schema (`Guild_Name, Year, Quarter, Market_Share_Pct, Employee_Count, Customer_Satisfaction_Score`), used to prove the agent/prompt/tool pipeline isn't secretly tied to the first file's column names
- **Realms:** invented fantastical lands (e.g. "Oasis of Whispering Sands", "Peak of the Sleeping Djinn") — deliberately not real countries
- **Guilds:** in-universe trading houses/guilds (e.g. "Djinn-Forged Ironworks", "Forty Thieves Foundry")
- **Years:** 717–718 — the historical Umayyad siege of Constantinople, the event the Sharrkan/Zau al-Makan story is loosely modeled on

**Why this story specifically:** the tale has genuine treasury/business texture — e.g. the bath-attendant (hammam keeper) who helps Zau al-Makan also runs his own trade — which maps naturally onto a financial-ledger dataset. Future synthetic data or flavor text for this project can keep drawing on this same story for consistency.

---

## Streamlit UI Design Direction (decided 2026-07-31)

Design mockup approved (as an Artifact, "Bazaar Books — Streamlit UI concept").
Not built yet — this documents the decision so it survives context resets.
Behavior stays intentionally basic (standard chat, no gimmicks); only the
visual identity is custom. **Everything below is achievable through
Streamlit's `.streamlit/config.toml` `[theme]` section + `st.chat_message`'s
`avatar` parameter — no custom CSS injection required**, verified against
current (2026) Streamlit docs before proposing it.

**Color tokens** (desert-night / lamplight, not the generic warm-cream +
terracotta palette most AI-generated designs default to):
- `--bg-night` `#14101f` — main chat background
- `--bg-lamp` `#0d0a17` — sidebar background (darker: "inside the lamp")
- `--accent-gold` `#c6963e` — assistant/djinn accent (muted brass, not neon)
- `--accent-teal` `#3f8079` — user accent (mosaic-tile teal, not terracotta)
- `--text-sand` `#e7dfc6` — primary text (warm parchment, not stock cream)
- `--text-muted` `#8f8570` — secondary/caption text

**Type tokens:**
- Display (`headingFont`, used sparingly — app title only): `Amiri` — Arabic/Latin calligraphic serif, dignified rather than kitschy
- Body (`font`): `Alegreya` — literary serif built for long-form reading
- Utility (tool-call/debug log text): `JetBrains Mono` — keeps the transparency log ("used execute_python_code with...") visually distinct from the narrative voice

**Layout concept:** two-zone — a narrow darker sidebar ("inside the lamp": data source picker, debug toggle, reset) and a wide main chat stage ("desert night"). Assistant messages get a thin gold left-border rule (light escaping the lamp); user messages get a thin teal right-border rule (mosaic tile). Charts from `create_chart` render inline in the message flow, framed, never in a popup.

**Chat personas:** assistant avatar `🧞`, user avatar `📜` (a nod to the README's own tagline, "whisper your question to the tabular scroll"). Composer placeholder text reuses that exact tagline instead of a generic "Ask a question...".

**Single-theme, deliberately:** no light-mode variant planned — a lit lamp against daylight doesn't carry the same feeling, so this commits to one visual world rather than trying to support both.

**Still open when this gets built:** whether `create_chart`'s matplotlib output should also be re-themed (via `matplotlib.rcParams`) to match this palette, or left as default matplotlib styling — not decided yet.

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
Add `.py` modules alongside the notebook once code stabilizes — **the
notebook is not being deleted or replaced**; it stays as the running R&D
log of every step, for anyone reading the repo to follow the reasoning.
The modules are an additional reusable layer that Streamlit (and future
code) imports from, so logic doesn't have to be copy-pasted out of the
notebook. Verified against the official `application-structure` docs and
the real `langchain-ai/react-agent` and `retrieval-agent-template` repos
(2026-07-28) — `nodes.py` and `build_agent()` are NOT used in any current
official template, so we drop them:
- `state.py` — NOT a LangGraph TypedDict state (we don't use raw
  `StateGraph`, we use `create_agent` which manages its own internal
  state). Here it just holds the current `df` (a get/set pair), since
  `tools.py` and `prompts.py` both need to read whichever table is
  currently loaded, and a plain module-level variable in one file doesn't
  work once the code is split across files.
- `tools.py` — `execute_python_code`, `create_chart`
- `prompts.py` — `build_schema_table`, `build_preview_kv`,
  `SYSTEM_PROMPT_TEMPLATE`, `build_system_prompt`
- `graph.py` — the `model` and a `build_agent(df)` function that sets the
  active table in `state`, builds the system prompt, and returns a fresh
  `create_agent(...)` — not a module-level `build_agent()` factory with no
  arguments; ours takes `df` because the table changes at runtime (file
  upload), unlike the official templates' static graphs
- No official project-structure guidance exists yet for the newer
  `create_agent` (`langchain.agents`) API we're actually using — this layout
  is our own reasonable choice, not a documented standard for that API

### Notebooks
- Names: `NN_description.ipynb` (leading number for order).
- `r&d.ipynb` keeps growing as the permanent step-by-step R&D record —
  it is never trimmed down once modules exist. Modules hold the reusable
  logic; the notebook is the narrative of how it got there.

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
- [x] MVP: synthetic dataset (`bazaar_books/caravan_accounts.csv`), schema+preview
      system prompt, `execute_python_code` tool, agent via `create_agent`
      (not the deprecated `create_react_agent`), first end-to-end queries
      confirmed working ("highest net income by realm", "most profitable
      company" — agent correctly maps natural-language terms to columns)

### Validated (2026-07-29)
Ran the agent against reference questions adapted from the legacy Forvis
Mazars assistant's sample queries + this project's README samples: single
aggregation, per-quarter grouping, growth-over-time, qualitative "why"
reasoning, and small talk. The generic `execute_python_code` tool + LLM
reasoning alone handled **all of them correctly** once `max_tokens` was
raised from 2048 to 8192 (Qwen3's hidden `<think>` reasoning was hitting the
old limit before producing visible output — confirmed via `finish_reason`
and `completion_tokens` in `response_metadata`). No case so far where the
generic tool proved insufficient — dedicated per-operation tools are
deprioritized until we hit a real one (see Next up, bottom item).

### Done (2026-07-30)
- Guard `execute_python_code` against printing huge output — truncates past
  `MAX_TOOL_OUTPUT_CHARS` with a clear message telling the model to narrow
  its query, instead of flooding the LLM context. Verified with a
  simulated large-output test (our real dataset is too small to trigger it
  naturally).
- Test user file upload in the notebook — `load_table(path)` generalizes
  loading beyond the one hardcoded CSV (verified against a second
  synthetic dataset, `guild_ledger.csv`, with an unrelated schema), plus a
  real click-to-upload flow via `ipywidgets.FileUpload`, tested against
  both a synthetic file and a real one (`data/new_fin.csv`, output not
  committed).
- `create_chart` tool — mirrors `execute_python_code`'s shape (LLM writes
  matplotlib code against `df`), saves the figure to `outputs/*.png`
  (git-ignored) and returns the path. System prompt updated so the agent
  knows to use it for chart/plot/visualization requests. Verified
  end-to-end through the agent, not just called directly.

### Done (2026-07-31)
- Extracted code into a `finanalyticsagent/` package alongside the notebook
  (flat layout, not `src/`-layout — that idea is noted for later, see
  bottom of Next up): `active_table.py`, `tools.py`, `prompts.py`,
  `graph.py`, `testing.py`. Verified standalone (independent of any
  notebook cell having run) both via direct script and by the user running
  Step 10 live in their own Jupyter session.
- Streamlit UI visual design direction decided (see "Streamlit UI Design
  Direction" section above) — design tokens and layout concept, confirmed
  against current Streamlit theming docs.

### Done (2026-08-01)
- Built the Streamlit UI (`app.py`, phase 3 — MVP complete) per the design
  direction above: sidebar (data source picker, tool-transparency toggle
  on by default, reset button), chat via `st.chat_message`/`st.chat_input`,
  `st.spinner` while the agent works, chart images shown inline with a
  download button. Model name (`finanalyticsagent.graph.MODEL_NAME`)
  surfaced in the header caption.
- Hardened the system prompt after live review surfaced real leaks:
  small talk no longer mentions "DataFrame"/"pandas"/"df" and stays short;
  the assistant never repeats `create_chart`'s raw file path or says
  "you can download this file" (the UI already shows the image + a real
  download button, so that text was both leaky and untrue); the key
  answer value is now consistently wrapped in markdown bold.
- Tool-usage transparency in the UI shows the literal tool name
  (`execute_python_code`/`create_chart`) — the "1001 Nights" theming
  stays in the data and visual design, not in how the assistant reports
  its own actions; that boundary matters and is now enforced in code,
  not just prose.

### Next up
1. Add a real `pytest` test suite in `tests/`. No formal tests exist yet —
   the notebook's manual check cells (e.g. the guard-test cell) don't move
   anywhere, since `r&d.ipynb` never gets trimmed per its own rule above;
   real tests get written fresh, not migrated from there.

   **Pure/deterministic unit tests (no LLM calls) — do these first:**
   - `build_schema_table`/`build_preview_kv` — known small DataFrame in,
     exact markdown/KV string out
   - `tools.load_table` — raises `ValueError` on an unsupported extension
   - `tools.execute_python_code`'s truncation guard — triggers at exactly
     `MAX_TOOL_OUTPUT_CHARS`, message says to narrow the query
   - `tools.create_chart` — returns an "Error: no chart was drawn" message
     when the code never calls a plotting function
   - `active_table.get_df()` — raises `RuntimeError` when nothing was set

   **Coarse LLM-in-the-loop regression checks (non-deterministic, but
   still worth automating as a substring/pattern check on the agent's
   final answer) — each one caught a real bug during Streamlit UI review
   (2026-08-01), so each is a genuine regression risk, not hypothetical:**
   - Small talk ("hi", "what can you do") never mentions "DataFrame",
     "pandas", or "df", and stays short (not a capability essay)
   - The final answer never contains a raw file path (e.g. `outputs/` or
     `.png`) or phrases like "you can download this file"
   - The final answer's key value is wrapped in markdown `**bold**`
   - `create_chart` questions actually produce a `.png` file that exists
     on disk, with a transparent background (alpha=0 at a corner pixel)
3. Multi-file support (upload arbitrary tables)
4. RAG module (Chroma) for non-tabular files (PDF/DOC)
   - File-type router: tabular → pandas tools, PDF/DOC → RAG
   - Router decides by file content and/or extension
   - Graceful degradation: if the RAG module/embedding endpoint is
     unavailable, tell the user explicitly instead of failing silently —
     matters for demos to colleagues
   - Embedding model currently only runs locally via Ollama; need a plan
     for running embedding models within the existing Mac/MLX setup instead
5. Conversation memory across sessions
6. Model backend switcher — local LLM stays primary, but add the ability to
   swap in Azure OpenAI / OpenAI endpoints (or other local models like
   DeepSeek) without rewriting the agent code. Note: `app.py`'s caption
   "nothing leaves this network" is only true for the on-prem stack — once
   remote endpoints are switchable, that text needs to become conditional
   on which backend is active, not a hardcoded claim
7. *(lowest priority, exploratory)* Dedicated functions/tools for common
   table operations (groupby-aggregate, filter, growth-over-time) as an
   alternative to the generic `execute_python_code` tool — only revisit if
   we hit a real question the generic tool can't handle; so far it has
   handled everything thrown at it
8. *(lowest priority, exploratory)* Move `finanalyticsagent/` into a
   `src/finanalyticsagent/` layout — deliberately deferred once already
   (2026-07-31), the user wanted to see the flat module split working
   first before adding directory nesting on top

---

## Rules for Claude Code

- **Verify current library APIs.** LangChain and LangGraph both hit v1.0 in April 2026 with breaking changes. Don't rely on 2024 documentation patterns.
- **The model is Qwen3-8B, not GPT-4.** Prompts must be explicit; tool docstrings thorough; small models need more guidance.
- **Ask before destructive actions:** rewriting git history, `git push --force`, deleting files, restructuring project layout.
- **Announce non-trivial actions before doing them.** Especially git operations, file moves, dependency installs.
- **Never hardcode credentials.** All secrets in `.env`.
- **Never commit real data.** The entire `data/` directory (except `.gitkeep`) is git-ignored on purpose — use the synthetic files in `bazaar_books/` for anything that needs to go into git or a notebook output.
- **Prefer the fastest path to a working prototype.** This is a personal MVP, not a production system. Don't propose custom implementations when a prebuilt one works. Don't refactor unless asked.
- **Never edit `r&d.ipynb` without an explicit go-ahead in the current message.** Editing it while the user might run cells causes real VS Code/Jupyter buffer desync (recurring, not hypothetical — happened multiple times). Wait for an explicit yes each time, not a standing blanket permission from earlier in the conversation.
- **Before editing `r&d.ipynb`, ask a short pre-flight check first** — e.g. "About to edit the notebook — have you saved it, and did you run anything I might not know about?" One quick question here prevents the VS Code/Jupyter desync above and confirms both sides agree on the current state before anything gets written.
- **`git commit`/`git push` require their own explicit go-ahead, separate from permission to make the underlying code changes.** "Fix X" or "apply the changes" is not "commit and push it" — those are two different requests. Ask before committing even when the changes themselves were requested and already made, especially right after edits the user hasn't personally verified yet.
- **When asked "why did X happen" or similar, answer the question first — do not start fixing.** Only fix once the user explicitly asks for a fix. Diagnosing and repairing in the same breath skips the user's chance to decide whether/how it should be fixed.
- **Update README.md/CLAUDE.md roadmap checkboxes right after finishing the step they describe, not several turns later.** Design decisions and completed work (e.g. the Streamlit design direction, module extraction) should get written down promptly — don't let documentation lag behind work that's already done, especially since context can reset and undocumented decisions are expensive to redo.
- **The r&d.ipynb-specific rules above generalize to every project file, not just the notebook.** This has bitten us on `app.py` too (editing it right after the user said "I don't like this" when they were flagging a concern, not asking for a fix — same mistake as the notebook desync pattern, just a different file). If a message reads as "noting/discussing/flagging" rather than a clear "do X now," don't edit anything — ask which it is first.
- **Default to assuming a message is discussion, not a command — this project runs on long, thorough back-and-forth before action is the norm, not the exception.** Hedged phrasing ("maybe," "what if," "could we," "может быть") is *not* a go-ahead, even when it sounds like a good idea worth acting on immediately. This has recurred multiple times (`r&d.ipynb`, `app.py`, and again on "may be we should add something to CLAUDE.local.md" — that last one was read as permission and shouldn't have been). Only a clear imperative ("do it," "fix this," "add X now") counts as authorization to edit. When genuinely unsure, ask in one line rather than guess — guessing wrong here has cost real rework and frustration repeatedly.
- **Roleplay/theming stays in the data and visual decoration, never in how the assistant reports its own behavior.** The "1001 Nights" flavor belongs to the synthetic dataset, chat personas, and color/type design — not in tool-usage transparency text, error messages, or anything describing what the code actually did. E.g. show the literal tool name (`execute_python_code`), not a themed rename like "consulted the ledger." This distinction was explicitly requested and is a standing design principle, not a one-off preference.