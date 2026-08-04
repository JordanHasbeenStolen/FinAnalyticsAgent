"""Streamlit chat UI for FinAnalyticsAgent.

Standard chat behavior (st.chat_message/st.chat_input, session_state for
history) — only the visual identity is custom, via .streamlit/config.toml.
See CLAUDE.md's "Streamlit UI Design Direction" for the design rationale.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from finanalyticsagent.graph import MODEL_NAME, answer_was_truncated, build_agent

DEMO_FILES = {
    "Demo ledger (financial)": "bazaar_books/caravan_accounts.csv",
    "Demo ledger (KPIs)": "bazaar_books/guild_ledger.csv",
    "Demo ledger (regions)": "bazaar_books/realm_metadata.csv",
}

st.set_page_config(page_title="The Djinn Financier", page_icon="🧞")


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Load a Streamlit-uploaded file into a DataFrame, by extension.

    Args:
        uploaded_file: the object returned by st.file_uploader.

    Returns:
        The loaded DataFrame.
    """
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def unique_table_name(name: str, existing: dict) -> str:
    """Avoid clobbering a table if two selected files share the same name.

    Args:
        name: the proposed table name (a file's stem).
        existing: the tables dict built so far.

    Returns:
        `name` if it's free, otherwise `name` with a numeric suffix.
    """
    if name not in existing:
        return name
    suffix = 2
    while f"{name}_{suffix}" in existing:
        suffix += 1
    return f"{name}_{suffix}"


with st.sidebar:
    st.markdown("### Data source")
    selected_demos = st.multiselect(
        "Demo datasets",
        list(DEMO_FILES),
        default=[next(iter(DEMO_FILES))],
    )
    uploaded_files = st.file_uploader(
        "Upload your own .csv/.xlsx (you can pick more than one)",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
    )

    tables: dict[str, pd.DataFrame] = {}
    for label in selected_demos:
        path = DEMO_FILES[label]
        tables[Path(path).stem] = pd.read_csv(path)
    for uploaded_file in uploaded_files:
        name = unique_table_name(Path(uploaded_file.name).stem, tables)
        tables[name] = load_uploaded_file(uploaded_file)

    if not tables:
        st.info("Select a demo dataset or upload a file to begin.")
        st.stop()

    source_key = (tuple(sorted(selected_demos)), tuple(f.name for f in uploaded_files))

    show_debug = st.checkbox("Show which tool was used", value=True)

    memory_window = st.slider(
        "Conversation memory (previous messages)",
        min_value=0,
        max_value=20,
        value=3,
        help="How many earlier messages the djinn remembers (a 'sliding "
        "window'). Lower this if answers start taking too long or the app "
        "struggles.",
    )

    if st.button("↺ Reset conversation"):
        st.session_state.messages = []
        st.rerun()

# Rebuild the agent only when the *set* of loaded tables actually changes —
# not on every rerun, since Streamlit reruns this whole script on every
# interaction.
if st.session_state.get("source_key") != source_key:
    st.session_state.agent = build_agent(tables)
    st.session_state.source_key = source_key
    st.session_state.messages = []

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🧞 Whisper your question to the tabular scroll")
st.caption(f"a djinn bound to a local model ({MODEL_NAME}) — nothing leaves this network")

for message in st.session_state.messages:
    avatar = "🧞" if message["role"] == "assistant" else "📜"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message.get("tool_note") and show_debug:
            st.caption(message["tool_note"])
        if message.get("image"):
            st.image(message["image"], width=380)
            with open(message["image"], "rb") as image_file:
                st.download_button(
                    "Download chart",
                    data=image_file,
                    file_name=Path(message["image"]).name,
                    mime="image/png",
                    key=f"download_{message['image']}",
                )

question = st.chat_input("Whisper your question to the tabular scroll...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="📜"):
        st.markdown(question)

    # Include up to `memory_window` earlier messages (the current question is
    # already the last entry in st.session_state.messages, appended above).
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[-(memory_window + 1) :]
    ]

    with st.spinner("🧞 Summoning an answer from the ledger..."):
        try:
            result = st.session_state.agent.invoke({"messages": history})
        except Exception:
            st.error(
                "The djinn is taking too long to answer. Try lowering "
                '"Conversation memory" in the sidebar, or ask a shorter question.'
            )
            st.stop()

    if answer_was_truncated(result):
        st.error("The answer got cut off before it was finished. Please try again.")
        st.stop()

    tool_names_used = [
        call["name"]
        for ai_message in result["messages"]
        if ai_message.type == "ai"
        for call in ai_message.tool_calls
    ]
    # De-duplicated, order preserved. Literal tool names, no renaming —
    # the theming stays in the data/UI decoration, not in how the
    # assistant reports its own actions.
    seen = []
    for name in tool_names_used:
        if name not in seen:
            seen.append(name)
    if seen:
        label = "Tool" if len(seen) == 1 else "Tools"
        tool_note = f"✨ {label} used: {', '.join(seen)}"
    else:
        tool_note = None

    image_path = None
    for tool_message in result["messages"]:
        if tool_message.type == "tool" and tool_message.name == "create_chart":
            content = tool_message.content
            if isinstance(content, str) and content.endswith(".png"):
                image_path = content

    final_answer = result["messages"][-1].content

    with st.chat_message("assistant", avatar="🧞"):
        st.markdown(final_answer)
        if tool_note and show_debug:
            st.caption(tool_note)
        if image_path:
            st.image(image_path, width=380)
            with open(image_path, "rb") as image_file:
                st.download_button(
                    "Download chart",
                    data=image_file,
                    file_name=Path(image_path).name,
                    mime="image/png",
                    key=f"download_{image_path}",
                )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": final_answer,
            "tool_note": tool_note,
            "image": image_path,
        }
    )
