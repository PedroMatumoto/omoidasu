import streamlit as st

import openai
from dotenv import find_dotenv, load_dotenv

from transcript import transcribe_audio
from chatting import chat

_ = load_dotenv(find_dotenv())

client = openai.OpenAI()


def tab_recorder():
    st.markdown("tab_recorder")


def tab_summarizer():
    st.markdown("tab_summarizer")


def main():
    st.set_page_config(
        page_title="Omoidasu - Meeting Synthesizer",
        page_icon=":robot:",
        layout="wide",
    )

    st.header("Omoidasu - Meeting Synthesizer", divider=True)
    st.write(
        "Omoidasu is an AI assistant that helps summarize meetings and create meeting minutes. "
        " It can assist in organizing the information discussed and producing a clear and concise summary."
    )

    ui_tab_recorder, ui_tab_summarizer = st.tabs(
        ["Meeting Recorder", "Meeting Summaries"]
    )
    with ui_tab_recorder:
        tab_recorder()
    with ui_tab_summarizer:
        tab_summarizer()


if __name__ == "__main__":
    main()
