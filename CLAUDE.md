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
- **Documents (RAG prototype):** `pymupdf` (pdf), `python-docx` (docx), `langchain-text-splitters` (direct dependency — was only pulled in transitively via the now-removed `langchain-community`)
- **UI:** Streamlit (`app.py`)

Dependencies are in `pyproject.toml`, locked in `uv.lock`. Add new packages via `uv add <package>`.

---

## Architecture

**ReAct pattern**, built with `create_agent` from `langchain.agents` (verified 2026-07-28:
`create_react_agent` from `langgraph.prebuilt` is now deprecated in favor of this).

### Tools
- `execute_python_code(code: str)` — runs LLM-generated pandas code against the loaded table(s) (a `dfs` dict, accessed as `dfs['table_name']`), returns the result. Truncates output past `MAX_TOOL_OUTPUT_CHARS` with a clear message instead of flooding the LLM context.
- `create_chart(code: str)` — matplotlib chart generation against `dfs`, saves PNG to `outputs/` (git-ignored, same rationale as `data/`), returns file path
- `load_table(path)` — loads a `.csv`/`.xlsx` by extension; this is the built version of what the roadmap used to call `read_new_table(path)`. Combined with `ipywidgets.FileUpload` in the notebook for a real click-to-upload flow.
- `search_documents(query: str)` — naive keyword search over PDF/DOCX chunks (RAG Stage 1). Prototype only, in `r&d.ipynb` (Step 13) — not yet in `finanalyticsagent/`/`app.py`.

### State
`TypedDict` with `messages: Annotated[list[AnyMessage], operator.add]`.

### Memory
Not LangGraph's `MemorySaver`/`thread_id` — deliberately avoided, since it
would fight Streamlit's rerun-every-interaction model more than it'd help.
Instead, `app.py` builds the message history to send from a plain
`st.session_state.messages` slice (a sidebar slider controls how many prior
messages, default 3) — in-session only, resets on "↺ Reset conversation" or
a full app restart. See `CHANGELOG.md` (2026-08-02) for how this was found
and fixed.

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
  - `bazaar_books/realm_metadata.csv` — a third synthetic dataset (`Realm, Region`), used in the multi-file support prototype (`r&d.ipynb` Step 12) as the table with no column in common with `guild_ledger` — a question needing both must bridge through `caravan_accounts`, which shares a column with each
- **Realms:** invented fantastical lands (e.g. "Oasis of Whispering Sands", "Peak of the Sleeping Djinn") — deliberately not real countries
- **Guilds:** in-universe trading houses/guilds (e.g. "Djinn-Forged Ironworks", "Forty Thieves Foundry")
- **Years:** 717–718 — the historical Umayyad siege of Constantinople, the event the Sharrkan/Zau al-Makan story is loosely modeled on

**Why this story specifically:** the tale has genuine treasury/business texture — e.g. the bath-attendant (hammam keeper) who helps Zau al-Makan also runs his own trade — which maps naturally onto a financial-ledger dataset. Future synthetic data or flavor text for this project can keep drawing on this same story for consistency.

---

## Streamlit UI Design Direction

Design mockup approved (as an Artifact, "Bazaar Books — Streamlit UI concept"),
built in `app.py` (see `CHANGELOG.md`, 2026-08-01). Kept here as ongoing
reference for the design tokens/rationale, not just a historical decision.
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

**Resolved:** `create_chart`'s matplotlib output is re-themed to match this palette — see `tools.py`'s `CHART_STYLE` (transparent figure/axes, the same gold/muted-sand colors, validated for contrast via the `dataviz` skill's palette checker).

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
`.py` modules live alongside the notebook (**the notebook is not being
deleted or replaced** — it stays as the running R&D log; the modules are a
reusable layer that Streamlit and tests import from):
- `active_table.py` — holds the currently active tables as a
  `dict[str, pd.DataFrame]` (`set_tables`/`get_tables`). Not a LangGraph
  `TypedDict` state — we don't use raw `StateGraph`, `create_agent` manages
  its own internal state; this just lets `tools.py`/`prompts.py` both read
  whichever tables are currently loaded. The old single-table `set_df`/
  `get_df` are kept as `@warnings.deprecated` shims (PEP 702), only so
  `r&d.ipynb`'s Step 10 keeps working unmodified.
- `tools.py` — `execute_python_code`, `create_chart`
- `prompts.py` — `build_schema_table`, `build_preview_kv`,
  `SYSTEM_PROMPT_TEMPLATE`, `build_system_prompt`
- `graph.py` — the `model` and `build_agent(tables)`, which takes a
  `dict[str, pd.DataFrame]` (a single DataFrame is also accepted,
  deprecated, wrapped internally as `{"df": tables}`) since the active
  tables change at runtime (file upload)

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

Dated history of completed/validated work moved to `CHANGELOG.md` (2026-08-04
— kept CLAUDE.md focused on active/current content, per Claude Code's own
documented guidance that files over ~200 lines "consume more context and may
reduce adherence").

### Next up
1. Harden `prompts.py` against the `<image src="...png" />` leak found above
   — the current wording only forbids prose mentions of the file path/
   "download this file", not markup that embeds it.
2. RAG module (Chroma) for non-tabular files (PDF/DOC) — phased plan:
   - [x] Stage 1 (2026-08-04): `search_documents` tool added to the existing
     agent in `r&d.ipynb` (Step 13). Naive keyword search, no embeddings,
     no Chroma. Loaders: `pymupdf` (pdf), `python-docx` (docx) — not
     `langchain_community`
   - [ ] Stage 2: real Chroma + embeddings, extracted into
     `finanalyticsagent/` + wired into `app.py`. Embedding model + Chroma
     persistence not decided yet
   - [ ] Stage 3 (ongoing): multi-agent (router + separate document agent),
     Docling for `.docx` only, Chroma vs Qdrant, scaling by model backend
   - **Reminder: update `docs/screenshot.png`** when RAG lands — it's
     already stale (shows the old single-file radio-button sidebar, not
     the current multi-file multiselect), but the change is cosmetically
     minor, so bundling it with the next visible UI change (RAG) rather
     than doing a screenshot-only update now
3. *(lowest priority, exploratory)* True persistence across app restarts —
   in-session memory is done (see above); this would need writing history
   to disk/a database, only worth it if the in-session-only version proves
   insufficient in practice
4. Model backend switcher — local LLM stays primary, but add the ability to
   swap in Azure OpenAI / OpenAI endpoints (or other local models like
   DeepSeek) without rewriting the agent code. Note: `app.py`'s caption
   "nothing leaves this network" is only true for the on-prem stack — once
   remote endpoints are switchable, that text needs to become conditional
   on which backend is active, not a hardcoded claim
5. *(lowest priority, exploratory)* Dedicated functions/tools for common
   table operations (groupby-aggregate, filter, growth-over-time) as an
   alternative to the generic `execute_python_code` tool — only revisit if
   we hit a real question the generic tool can't handle; so far it has
   handled everything thrown at it
6. *(lowest priority, not urgent — revisit next time a similarly
   heavy/resource-intensive question comes up)* `request_timeout=180` on
   the model only bounds a single HTTP request, not the whole
   `agent.invoke()` call — a ReAct loop makes 2+ sequential model calls
   (decide tool call, then synthesize the final answer), so the *total*
   user-visible wait isn't actually capped at 180s. Measured 2026-08-04: a
   hard 3-table transitive-join question took **286.9s** end to end (vs.
   57-70s for similarly-shaped questions) without tripping the timeout,
   since no single one of its underlying calls individually exceeded 180s.
   Would need an overall deadline wrapped around the whole `invoke()` call,
   not just the client's per-request timeout — not done now, just recorded
   so we know to revisit it if/when a heavy task like this resurfaces.
7. *(lowest priority, exploratory)* Move `finanalyticsagent/` into a
   `src/finanalyticsagent/` layout — deliberately deferred once already
   (2026-07-31), the user wanted to see the flat module split working
   first before adding directory nesting on top
8. *(lowest priority, exploratory)* Scaling multi-file support to many
   tables (10-30+) — current design dumps every loaded table's full
   schema+preview into the system prompt on every question, which doesn't
   scale: bigger prompt, slower responses, and untested (likely worse)
   table-selection accuracy among many tables. Only tested up to 3. If
   this is ever needed, the fix is lazy disclosure — list table names +
   one-line descriptions upfront, add a `describe_table(name)` tool the
   model calls on demand — not just raising a number. Not pursued now;
   current roadmap scope is a handful of files (2-5)

---

## Rules for Claude Code

- **Verify current library APIs.** LangChain and LangGraph both hit v1.0 in April 2026 with breaking changes. Don't rely on 2024 documentation patterns.
- **Before introducing any new module, library, testing framework, or architectural pattern — verify against current official sources that it's genuinely still the industry standard**, not just that it works or matches confident recall. This is a common failure mode: presenting an outdated-but-plausible choice as current fact. Already happened in this project: `import fitz` presented as current PyMuPDF usage when the installed version's primary name is now `pymupdf`; an initial multi-agent architecture proposal leaned on outdated patterns before dedicated research corrected it. Applies to the high-level choice (is this library/pattern still what's used) as much as the low-level API call.
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