"""Streamlit chat UI for FinAnalyticsAgent.

Standard chat behavior (st.chat_message/st.chat_input, session_state for
history) — only the visual identity is custom, via .streamlit/config.toml.
See CLAUDE.md's "Streamlit UI Design Direction" for the design rationale.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from finanalyticsagent.graph import MODEL_NAME, build_agent

DEMO_FILES = {
    "Demo ledger (financial)": "bazaar_books/caravan_accounts.csv",
    "Demo ledger (KPIs)": "bazaar_books/guild_ledger.csv",
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


with st.sidebar:
    st.markdown("### Data source")
    choice = st.radio(
        "Data source",
        list(DEMO_FILES) + ["Upload your own file"],
        label_visibility="collapsed",
    )

    if choice == "Upload your own file":
        uploaded_file = st.file_uploader("Upload a .csv or .xlsx", type=["csv", "xlsx"])
        if uploaded_file is None:
            st.info("Upload a file to begin.")
            st.stop()
        active_df = load_uploaded_file(uploaded_file)
        source_key = uploaded_file.name
    else:
        active_df = pd.read_csv(DEMO_FILES[choice])
        source_key = choice

    show_debug = st.checkbox("Show which tool was used", value=True)

    if st.button("↺ Reset conversation"):
        st.session_state.messages = []
        st.rerun()

# Rebuild the agent only when the data source actually changes — not on
# every rerun, since Streamlit reruns this whole script on every interaction.
if st.session_state.get("source_key") != source_key:
    st.session_state.agent = build_agent(active_df)
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

    with st.spinner("🧞 Summoning an answer from the ledger..."):
        result = st.session_state.agent.invoke({"messages": [{"role": "user", "content": question}]})

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
