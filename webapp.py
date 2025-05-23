from pathlib import Path
from datetime import datetime
import time
import queue
import imageio_ffmpeg
from streamlit_webrtc import WebRtcMode, webrtc_streamer
import streamlit as st
import pydub

import openai
from dotenv import find_dotenv, load_dotenv

from transcript import transcribe_audio, transcribe_in_chunks
from chatting import chat
from utils import (
    get_meeting_title,
    save_text_file,
    read_text_file,
    generate_abstract,
    generate_pdf,
    delete_all_files,
)

DIR_FILES = Path(__file__).parent / "files"
DIR_FILES.mkdir(exist_ok=True)

_ = load_dotenv(find_dotenv())

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
pydub.AudioSegment.converter = ffmpeg_path


def add_audio_chunk(audio_frame, audio_chunk):
    """
    Add audio frames to the audio chunk.
    Args:
        audio_frame: Audio frame to be added.
        audio_chunk: Audio chunk to which the frame will be added.
    Returns:
        Audio chunk with the added frame.
    """
    for frame in audio_frame:
        audio_chunk += pydub.AudioSegment(
            data=frame.to_ndarray().tobytes(),
            sample_width=frame.format.bytes,
            frame_rate=frame.sample_rate,
            channels=len(frame.layout.channels),
        )
    return audio_chunk


def list_meetings():
    """
    List all meetings in the directory.
    Returns:
        List of meeting directories.
    """
    meetings_list = DIR_FILES.glob("*")
    meetings_list = list(meetings_list)
    meetings_list.sort(reverse=True)
    meetings_dict = {}
    for meeting in meetings_list:
        meeting_date = meeting.stem
        year, month, day, hour, minute, second = meeting_date.split("-")
        title = read_text_file(meeting / "title.txt")
        meetings_dict[meeting_date] = (
            f"{year}/{month}/{day} {hour}:{minute}:{second} - {title}"
        )

    return meetings_dict


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
    dir_meeting = DIR_FILES / datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
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
                    save_text_file(dir_meeting / "transcription.txt", transcription)
                    save_text_file(
                        dir_meeting / "title.txt", get_meeting_title(transcription)
                    )

                    container.markdown(transcription)
                    audio_chunk = pydub.AudioSegment.empty()
        else:
            break


def tab_summarizer():
    # colcoar botao de deletar arquivos
    if st.button("Delete all files"):
        delete_all_files(DIR_FILES)
        st.success("All files deleted successfully!")

    dict_meetings = list_meetings()
    if not dict_meetings:
        st.warning("No meetings found.")
        return
    selected_meeting = st.selectbox(
        "Select a meeting", options=list(dict_meetings.values())
    )

    st.divider()
    meeting_date = list(dict_meetings.keys())[
        list(dict_meetings.values()).index(selected_meeting)
    ]
    dir_meeting = DIR_FILES / meeting_date
    format_date = datetime.strptime(meeting_date, "%Y-%m-%d-%H-%M-%S")
    meeting_date = format_date.strftime("%Y/%m/%d %H:%M:%S")
    title = read_text_file(dir_meeting / "title.txt")
    transcription = read_text_file(dir_meeting / "transcription.txt")
    abstract = read_text_file(dir_meeting / "abstract.txt")
    if abstract == "":
        generate_abstract(dir_meeting, transcription)
        abstract = read_text_file(dir_meeting / "abstract.txt")

    st.markdown(f"# **{title}**")
    st.markdown(f"## **Meeting Date:** {meeting_date}")
    st.markdown("### **Abstract:**")
    st.markdown(abstract)
    st.markdown("### **Download Meeting Minutes**")
    st.markdown(
        "Download the meeting minutes in PDF format. "
        "The minutes will be generated based on the transcription and abstract."
    )
    if st.button("Generate PDF"):
        pdf_path = dir_meeting / "meeting_minutes.pdf"
        generate_pdf(title, meeting_date, abstract, transcription, pdf_path)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Download Meeting Minutes PDF",
                data=pdf_file,
                file_name="meeting_minutes.pdf",
                mime="application/pdf",
            )
    st.markdown("### **Transcription:**")
    st.markdown(transcription)


def tab_file_uploader():
    st.subheader("Upload a meeting audio file")
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "ogg"])
    if uploaded_file is not None:
        if "last_uploaded_filename" not in st.session_state or st.session_state.last_uploaded_filename != uploaded_file.name:
            dir_meeting = DIR_FILES / datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            dir_meeting.mkdir(exist_ok=True)
            with open(dir_meeting / uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.last_uploaded_filename = uploaded_file.name
            st.session_state.dir_meeting = str(dir_meeting)
            st.success("File uploaded successfully!")
            st.audio(dir_meeting / uploaded_file.name, format="audio/mp3")
            st.markdown("Transcribing...")
            transcription = transcribe_in_chunks(
                dir_meeting / uploaded_file.name, language="pt"
            )
            save_text_file(dir_meeting / "transcription.txt", transcription)
            save_text_file(dir_meeting / "title.txt", get_meeting_title(transcription))
            st.session_state.transcription = transcription
            st.markdown("Transcription completed!")
            st.markdown(transcription)
            st.rerun()
        else:
            dir_meeting = Path(st.session_state.dir_meeting)
            st.success("File uploaded successfully!")
            st.audio(dir_meeting / uploaded_file.name, format="audio/mp3")
            st.markdown("Transcription completed!")
            st.markdown(st.session_state.transcription)


def main():
    st.set_page_config(
        page_title="Omoidasu - Meeting Synthesizer",
        page_icon="assets/logo_omoidasu.png",
        layout="wide",
    )

    st.image(
        "assets/banner-omoidasu.png", use_container_width=True
    )  # Adiciona imagem de banner
    st.header("思 Omoidasu - Meeting Synthesizer", divider=True)

    st.write(
        "Omoidasu is an AI assistant that helps summarize meetings and create meeting minutes. "
        " It can assist in organizing the information discussed and producing a clear and concise summary."
    )

    (
        ui_tab_recorder,
        ui_tab_file_uploader,
        ui_tab_summarizer,
    ) = st.tabs(["Meeting Recorder", "Upload Meeting", "Meeting Summaries"])
    with ui_tab_recorder:
        tab_recorder()
    with ui_tab_summarizer:
        tab_summarizer()
    with ui_tab_file_uploader:
        tab_file_uploader()


if __name__ == "__main__":
    main()
