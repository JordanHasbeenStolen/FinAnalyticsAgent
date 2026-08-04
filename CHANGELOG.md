# Changelog

Dated history of completed/validated work for FinAnalyticsAgent. Not read
into every Claude Code session (unlike `CLAUDE.md`) — check here for the
"what happened when" story; check `CLAUDE.md` for current status and the
active roadmap ("Next up").

## Done
- [x] Repo initialized, project structure in place
- [x] Dependencies installed via uv
- [x] Stack check passes — LLM responds via LangChain
- [x] MVP: synthetic dataset (`bazaar_books/caravan_accounts.csv`), schema+preview
      system prompt, `execute_python_code` tool, agent via `create_agent`
      (not the deprecated `create_react_agent`), first end-to-end queries
      confirmed working ("highest net income by realm", "most profitable
      company" — agent correctly maps natural-language terms to columns)

## Validated (2026-07-29)
Ran the agent against reference questions adapted from the legacy Forvis
Mazars assistant's sample queries + this project's README samples: single
aggregation, per-quarter grouping, growth-over-time, qualitative "why"
reasoning, and small talk. The generic `execute_python_code` tool + LLM
reasoning alone handled **all of them correctly** once `max_tokens` was
raised from 2048 to 8192 (Qwen3's hidden `<think>` reasoning was hitting the
old limit before producing visible output — confirmed via `finish_reason`
and `completion_tokens` in `response_metadata`). No case so far where the
generic tool proved insufficient — dedicated per-operation tools are
deprioritized until we hit a real one (see CLAUDE.md's roadmap).

## Done (2026-07-30)
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

## Done (2026-07-31)
- Extracted code into a `finanalyticsagent/` package alongside the notebook
  (flat layout, not `src/`-layout — that idea is noted for later, see
  bottom of CLAUDE.md's roadmap): `active_table.py`, `tools.py`, `prompts.py`,
  `graph.py`, `testing.py`. Verified standalone (independent of any
  notebook cell having run) both via direct script and by the user running
  Step 10 live in their own Jupyter session.
- Streamlit UI visual design direction decided (see CLAUDE.md's "Streamlit UI
  Design Direction" section) — design tokens and layout concept, confirmed
  against current Streamlit theming docs.

## Done (2026-08-01)
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

## Done (2026-08-02)
- Added a real `pytest` test suite in `tests/` — `pytest` is a dev-only
  dependency (`dependency-groups.dev` in `pyproject.toml`, per PEP 735, not
  the main `dependencies` list, since end users of the Streamlit app never
  need it).
  - **Pure/deterministic unit tests** (no LLM calls, sub-second):
    `test_prompts.py` (`build_schema_table`/`build_preview_kv`),
    `test_tools.py` (`load_table`'s `ValueError`, the truncation guard, the
    no-chart-drawn error), `test_active_table.py` (`get_df()`'s
    `RuntimeError`). `conftest.py` resets `active_table`'s module-level
    `_active_df` before/after every test to avoid state leaking between them.
  - **Coarse LLM-in-the-loop regression checks** (`test_agent_regressions.py`,
    needs a reachable `mlx_lm.server`, ~80s for the full layer): small talk never
    mentions "DataFrame"/"pandas"/"df", the chart answer never leaks a raw
    file path, the key answer value is bolded, `create_chart` produces a
    real transparent PNG. This layer already caught one real, previously
    unnoticed regression: the agent once wrapped the chart path in an
    `<image src="outputs/....png" />` tag — a leak the existing prompt
    wording didn't anticipate (it only forbade prose phrasing like "you can
    download this file"). The run is genuinely non-deterministic even with
    `temperature=0` (confirmed empirically — three identical requests with a
    fixed `seed=42` still produced three differently-worded answers, so this
    local model/server doesn't honor `seed` for reproducibility); the
    `<image src=...>` leak has not recurred since, but the prompt itself has
    **not** been hardened against it yet — still open, tracked in CLAUDE.md.
  - Both layers are also wired into `r&d.ipynb` as Step 11 (two `!python -m
    pytest ... --no-header` cells — `--no-header` keeps the local username/
    path out of committed cell output; bare `pytest`, without `python -m`,
    fails here with `ModuleNotFoundError` since `finanalyticsagent` isn't an
    installed package, only importable when the cwd is on `sys.path`).

## Done (2026-08-02, later same day)
- Gave the agent short-term conversation memory: `app.py` was passing only
  the current question to `agent.invoke()` on every turn (confirmed by
  reading the code, not assumed) — so the agent forgot everything after a
  single message, even within one open browser tab. Fixed with a manual
  sliding window (Path 1 — plain `st.session_state.messages` slicing, not
  LangGraph's `MemorySaver`/`thread_id`, which would fight Streamlit's
  rerun-every-interaction model more): a sidebar slider ("Conversation
  memory (previous messages)", default 3) controls how many prior messages
  get included. Paired with `request_timeout=180` on the model in
  `graph.py` — measured real per-answer latency first (20-26s for a simple
  lookup/chart/heavy-reasoning question each, via direct timed
  `agent.invoke()` calls against the live server) rather than guessing; 180s
  is a ~2-3x safety margin over the worst case, so a struggling Mac now
  surfaces a catchable error in the UI (with a hint to lower the memory
  slider) instead of hanging Streamlit forever.
  - **Scope note:** this is in-session memory only (per open browser tab,
    resets on "↺ Reset conversation" or a full app restart) — not
    persistence across app restarts/machine reboots. If that's ever needed,
    it's a different, bigger piece of work (e.g. writing history to disk or
    a database keyed by session), not attempted here.

## Done (2026-08-04)
- Multi-file support: the agent now answers using several named tables at
  once (`dfs['name']`), matching how the legacy Assistants API's Code
  Interpreter worked (files attached together all sit in one sandbox).
  Prototyped in `r&d.ipynb` (Step 12) against the real LLM first, then
  extracted into `finanalyticsagent/` — `active_table.py`'s
  `set_tables`/`get_tables`, `tools.py`, `prompts.py`, `graph.py` — with
  the old single-table API kept as `@warnings.deprecated` shims (PEP 702)
  so `r&d.ipynb`'s Step 10 needs zero changes. `app.py`'s sidebar now
  supports a multiselect over demo datasets plus multi-file upload.
  - Added `bazaar_books/realm_metadata.csv` as a real, tracked synthetic
    file (not built in-memory) for the prototype's transitive-join test.
  - Validated live: correct table selection among 3 loaded tables, and
    correct recognition/execution of a transitive bridge join (two tables
    sharing no column, connected through a third).
  - **Known, accepted limitation:** direct two-table joins are reliable
    (4/4 runs, always merging on every shared column), but the bridging
    merge in a transitive/3-table join consistently used only one shared
    column (4/4 runs), inflating row counts — harmless for the `mean()`-
    based questions tested so far, not for `sum()`/`count()`-based ones. A
    plain prompt instruction to merge on all shared columns didn't fix
    this across three attempts. Accepted as a known risk, not pursued
    further, per the project's practice of not solving a hypothetical
    problem ahead of a real one.
