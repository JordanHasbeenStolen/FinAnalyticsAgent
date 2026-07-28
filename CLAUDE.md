# CLAUDE.md

Context file for Claude Code. Read this file every time you enter this project — it defines the project and how we work together.

**Note:** There is also a `CLAUDE.local.md` (git-ignored) with additional personal context. Read it if it exists.

---

## 1. Project Overview

**FinAnalyticsAgent** is a personal on-prem AI oracle for spreadsheets — a LangGraph agent bound to a locally-hosted Qwen3-8B LLM that reads tabular data (CSV/XLSX) and answers natural-language questions about it: aggregations, insights, charts.

**Why this project exists:**
- A modern agentic replacement for legacy OpenAI Assistants API tabular analytics workflows
- Runs fully on-prem — no data sent to third-party APIs
- Serves as a portfolio piece and a hands-on application of LangGraph patterns
- Prototype now; future ambition is to grow into a reusable analytics engine with a Streamlit UI

Personal learning + portfolio project.

---

## 2. Tech Stack

- **Language:** Python 3.13.5
- **Package manager:** `uv` (not pip)
- **Environment:** WSL2 Ubuntu on Windows, VS Code + Jupyter
- **LLM:** `Qwen/Qwen3-8B-MLX-4bit` running via `mlx_lm.server` on a separate Apple Silicon Mac in the local network. Endpoint URL is stored locally, not committed.
- **Orchestration:** LangGraph 1.2.x
- **LangChain:** 1.3.x (v1.0 released April 2026 with breaking changes — don't rely on pre-1.0 patterns)
- **Data:** pandas, matplotlib, openpyxl (for XLSX)
- **UI (planned):** Streamlit

Dependencies are in `pyproject.toml` and locked in `uv.lock`. When you need a new package: `uv add <package>`.

---

## 3. Target Architecture

**ReAct pattern**, custom LangGraph agent (may be built manually rather than via `create_react_agent`, for learning value).

### Nodes
- `agent` — LLM node with system prompt, decides what tool to call or when to answer directly
- `tools` — executes tool calls
- Conditional edge based on `tool_calls` in the last AI message

### Tools
- `execute_python_code(code: str)` — runs LLM-generated pandas code against a pre-loaded DataFrame in a controlled exec context, returns the result
- `create_chart(code: str)` — matplotlib chart generation, saves PNG to `outputs/`, returns file path *(phase 2)*
- Future: `read_new_table(path)` for arbitrary table uploads in a Streamlit session

### State
`TypedDict` with `messages: Annotated[list[AnyMessage], operator.add]` (add-reducer pattern).

### Memory
`MemorySaver` for in-session continuity. `thread_id` = session identifier.

### Data flow
```
CSV loaded once → DataFrame in memory → tool operates on that DataFrame → LLM sees results as ToolMessage → formulates answer
```

The full DataFrame is **never** put into the LLM prompt. Only:
- Schema (column names + dtypes) in system prompt
- First 3-5 rows as preview in system prompt
- All actual queries via tools

---

## 4. About the Developer

### Background
- Humanitarian by training: computational linguistics + Master's in CS
- Came to LLM engineering through symbolic NLP (rule-based parsers Tomita/Yargy, GLR grammars) and knowledge graphs (FOAF, BFO/CCO ontologies, SPARQL, GraphDB)
- Several years in NLP and data engineering, focused on LLM engineering in the recent period
- Certified: Azure AI-102

### What I know well
- RAG systems (Azure OpenAI + AI Search, Qdrant, Chroma, embedding-based retrieval)
- Prompt engineering, especially tool docstrings-as-intents
- LangGraph core patterns: ReAct, Reflection, Routing, tool calling, state management, `MemorySaver`
- Local LLM deployment on Apple Silicon (MLX, Ollama, `mlx_lm.server`)
- Azure AI ecosystem, Semantic Kernel, MAF (Microsoft Agent Framework) orchestration patterns
- Data cleaning, SQL, Excel/Power BI reporting
- Knowledge representation (BFO/CCO, OWL/Turtle, SPARQL, rdflib)

### Cognitive quirks that matter for our work
- I learn slowly by choice — deep over fast. Don't rush me.
- I over-explore. If not kept in scope, I go 3 levels deeper than needed and lose time. Help me stay focused.
- I have a **treacherous feedback loop**: I ask a question → get an answer → feel relief → believe I understood → in fact I didn't retain it. Counteract this by making me explain things back in my own words, asking follow-up checks, catching where I'm floating.
- I'm a linguist — good analogies land better than dry theory. Metaphors, concrete examples, real scenarios beat abstract explanations.

---

## 5. How to Work With Me Effectively

### DO
- **Use SQL as the default analogy anchor.** SQL is my go-to mental model. `TypedDict` is like `CREATE TABLE`. `operator.add` is `INSERT` not `UPDATE`. `conditional_edge` is `CASE WHEN`. This works.
- **Explain classes as "boxes for data + functions"**, not through OOP philosophy. `self.x` = "belongs to this specific box". No inheritance/polymorphism unless absolutely necessary.
- **For list/dict comprehensions, show the expanded for-loop version first, then the one-liner as a shorthand.** Never the reverse.
- **Small commits.** Split work into commit-sized pieces. Conventional Commits format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- **Explain the "why", not just the "what".** Especially for LangGraph patterns — I want to understand the mechanics, not just paste code.
- **When you introduce a new term, define it inline.** Don't drop jargon and move on. "Delta" isn't self-explanatory; "reducer" isn't; "conditional edge" needs one sentence of grounding.
- **Verify library APIs.** LangChain and LangGraph both hit v1.0 in April 2026 with real breaking changes. Don't rely on 2024 patterns. When in doubt, check the current docs.
- **The model is Qwen3-8B, not GPT-4.** Smaller model, needs explicit prompts, thorough tool docstrings, clearer system instructions. Don't assume GPT-4-level reasoning.
- **Prefer explicit over clever.** No `functools.partial` if a wrapper function is clearer. No walrus operators. No metaclasses.
- **Ask before destructive actions:** rewriting git history, `git push --force`, deleting files, restructuring project layout.
- **Announce what you're going to do before doing it, when it's non-trivial.** Especially for git operations, file moves, dependency installs.

### DON'T
- **Don't give me polished answers I'll just read and nod at.** That's the feedback loop that kills my retention. Make me work for it — ask me back, quiz me on what I just said.
- **Don't sprint.** If you dump 15 steps at once, I'll get lost by step 4. Break into small units, confirm before moving on.
- **Don't defend mistakes.** If you were wrong, say so plainly. Don't add "but I was still right about X" — that's a defensive reaction I've called out multiple times.
- **Don't give up prematurely.** If you say "probably not supported" or "this is unfixable," verify with web search first. Assistants often collapse into "unfortunately this doesn't work" too early. You are better than that.
- **Don't tarabar** (rapid-fire bullet points with no explanation). Prose sentences, breathing room, one idea at a time.
- **Don't ignore my specific question.** Sometimes I ask a specific thing and get a general answer that circles the topic. Read my question carefully. Restate it in your head if needed.
- **Don't hardcode credentials.** Not tokens, not API keys, not URLs with tokens embedded. Everything sensitive goes into `.env` (already in `.gitignore`).
- **Don't touch data files.** Real data may end up in `data/` for testing. It's `.gitignore`'d. Never suggest committing it.

---

## 6. Stoppers (things that reliably block me)

- **Overwhelming instructions.** 15 sub-steps at once → I stall. Break into 3-5 max per message.
- **Undefined terms.** If I encounter a word I don't know, I might not stop you — but I stop learning. Define as you go.
- **Assumed context.** Don't assume I remember what we discussed 40 messages ago. Refer back explicitly if you're building on earlier context.
- **Tool/library changes I didn't opt into.** Don't switch approaches mid-project without asking. If we were doing X and you now want to do Y, explain why and get consent.
- **Rushed refactors.** "Let me just clean this up" often leaves me with code I no longer recognize. Refactor with narration, or don't.
- **Overwhelming choice.** "You could use A, B, C, D, or E — up to you" is paralyzing. Recommend one, note alternatives briefly, let me push back if I want.

---

## 7. Code Style Rules

### Python
- Python 3.13 features are OK (union types with `|`, structural pattern matching where truly clearer)
- **Type hints on public functions and tools.** Don't force them into every trivial internal helper — but for anything the LLM sees or the API exposes, yes.
- **Docstrings on every tool and every non-trivial function.** Tool docstrings especially matter — they go into the LLM's prompt. Multi-line, describe behavior, args, returns, and *when to use* the tool.
- **Prefer f-strings** over `.format()` or `%`.
- **`from module import name` style is fine and preferred for readability.** Don't rewrite existing `from x import Y` imports into fully-qualified ones.
- Group imports in this order: stdlib, third-party, local. Blank line between groups.

### LangGraph-specific
- **State classes go in `state.py`** when the project grows past a single notebook.
- **Node functions in `nodes.py` or split by node** when they grow beyond ~30 lines.
- **Tools in `tools.py`.**
- **The graph builder in `graph.py`** — a function like `build_agent() -> CompiledStateGraph`.
- **System prompts in `prompts.py`** as string constants. Don't inline them in graph code.

### Notebooks
- Use for exploration and rapid iteration, not final code.
- When something works in a notebook, extract to `.py` modules and import back in.
- Notebook names: `NN_description.ipynb` (leading number for order).

---

## 8. Git Workflow

- **Branch:** work on `main` for solo project. Feature branches only when experimenting with something we might discard.
- **Commit early, commit often.** Small commits with clear messages. Bad: "updates". Good: `feat: add execute_python_code tool with docstring`.
- **Never commit:** `.venv/`, `.env`, raw data files, notebook checkpoints, IDE configs. All in `.gitignore`.
- **Author identity:** locally configured for this repo (not global). Don't touch global config.
- **Remote:** HTTPS with fine-grained PAT. Don't suggest switching to SSH unless I ask.
- **Before push:** run `git status` and `git log origin/main..HEAD --stat` if anything feels uncertain.

---

## 9. Common Commands (reference)

### Environment
```bash
source .venv/bin/activate
uv add <package>          # install + track in pyproject.toml
uv sync                   # reinstall from lockfile
```

### Jupyter (in browser, when VS Code Jupyter misbehaves)
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

## 10. Current Status & Immediate Next Steps

### Done
- [x] Repo initialized, project structure in place
- [x] Dependencies installed via uv
- [x] Stack check passes — LLM responds via LangChain

### Next up (in order)
1. Load `new_fin.csv` into pandas, inspect schema
2. Design the schema-and-preview system prompt (what does the LLM see about the DataFrame?)
3. Build `execute_python_code` tool with proper docstring
4. Wire into a basic ReAct agent
5. First end-to-end query: "Which country had the highest net income in 2023?"
6. Iterate on more queries
7. Add `create_chart` tool (phase 2)
8. Move logic from notebook to `.py` modules
9. Streamlit UI (phase 3)

---

## 11. Communication Preferences

- **Language:** Russian in conversation, English in code, commits, and documentation.
- **Tone:** direct, respectful, not overly formal. You can disagree with me — that's more useful than agreeing.
- **Length:** match the question. Short question → short answer. Complex topic → structured explanation. Don't pad.
- **Explanations first, code second.** When you propose changes, describe the plan in prose before writing code.
- **After code, offer to verify:** "want me to run it?" or "should I add a test?" — don't just dump code and disappear.

---

## 12. Related Projects (for context)

- **Multi-agent Goetia Roleplay System** — parallel personal project. LangGraph multi-agent, 72 personas via runtime registry pattern, medium-agent routing with elicitation. Same tech stack (Qwen3 local, LangGraph, planned Streamlit).

---

## 13. Final Notes

- If you're unsure whether I understand something, **ask me to explain it back**. Don't just assume based on my "yeah" — I nod politely.
- If you catch yourself about to defend a wrong thing you said, **stop and say "I was wrong about X"** plainly. That's what I trust.
- If I'm asking for help with something you think is a bad idea, **push back once with reasoning**, then respect my choice if I still want it.
- The end goal isn't a perfect codebase. The end goal is that I understand LangGraph and agentic systems well enough to explain and defend design decisions.

Let's build something good.