from pathlib import Path
from datetime import datetime
import time
import queue
from streamlit_webrtc import WebRtcMode, webrtc_streamer
import streamlit as st
import pydub

import openai
from dotenv import find_dotenv, load_dotenv

from transcript import transcribe_audio
from chatting import chat

DIR_FILES = Path(__file__).parent / "files"
DIR_FILES.mkdir(exist_ok=True)

_ = load_dotenv(find_dotenv())

client = openai.OpenAI()


def add_audio_chunk(audio_frame, audio_chunk):
    for frame in audio_frame:
        audio_chunk += pydub.AudioSegment(
            data=frame.to_ndarray().tobytes(),
            sample_width=frame.format.bytes,
            frame_rate=frame.sample_rate,
            channels=len(frame.layout.channels),
        )
    return audio_chunk


def save_transcription(file_path, transcription):
    with open(file_path, "w") as f:
        f.write(transcription)


def tab_recorder():
    webrtx_ctx = webrtc_streamer(
        key="meeting_recorder",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=1024,
        media_stream_constraints={
            "video": False,
            "audio": True,
        },
    )

    if not webrtx_ctx.state.playing:
        return

    container = st.empty()
    container.markdown("Recording...")
    dir_meeting = DIR_FILES / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dir_meeting.mkdir(exist_ok=True)

    last_transcription = time.time()
    audio_chunk = pydub.AudioSegment.empty()
    full_audio = pydub.AudioSegment.empty()
    transcription = ""

    while True:
        if webrtx_ctx.audio_receiver:
            try:
                audio_frame = webrtx_ctx.audio_receiver.get_frames(timeout=1)
            except queue.Empty:
                time.sleep(0.1)
                continue
            full_audio = add_audio_chunk(audio_frame, audio_chunk)
            audio_chunk = add_audio_chunk(audio_frame, audio_chunk)
            if len(audio_frame) > 0:
                full_audio.export(dir_meeting / "audio.mp3", format="mp3")
                if time.time() - last_transcription > 10:
                    last_transcription = time.time()
                    audio_chunk.export(dir_meeting / "audio_chunk.mp3", format="mp3")
                    transcription_chunk = transcribe_audio(
                        dir_meeting / "audio_chunk.mp3"
                    )
                    transcription += transcription_chunk
                    save_transcription(dir_meeting / "transcription.txt", transcription)
                    container.markdown(transcription)
                    audio_chunk = pydub.AudioSegment.empty()
        else:
            break


def tab_summarizer():
    st.markdown("tab_summarizer")


def main():
    st.set_page_config(
        page_title="Omoidasu - Meeting Synthesizer",
        page_icon="assets/logo_omoidasu.png",
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
