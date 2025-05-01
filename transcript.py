import openai
from dotenv import find_dotenv, load_dotenv
from pydub import AudioSegment
import os
import streamlit as st
import imageio_ffmpeg


_ = load_dotenv(find_dotenv())

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
AudioSegment.converter = ffmpeg_path


def split_audio(file_path, chunk_length_ms=60000):
    """Splits the audio file into chunks of specified length."""
    audio = AudioSegment.from_file(file_path)
    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i : i + chunk_length_ms]
        chunk_path = f"{file_path}_chunk_{i // chunk_length_ms}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunks.append(chunk_path)
    return chunks


def transcribe_audio(
    file_path: str, language: str = "pt", response_format: str = "text"
) -> str:
    """response format can be 'text' or 'srt'"""
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            language=language,
            response_format=response_format,
        )
    return transcript


def transcribe_in_chunks(file_path: str, language: str = "pt") -> str:
    """Transcribe the audio file in chunks to avoid timeouts and memory issues."""
    chunk_paths = split_audio(file_path)
    full_transcript = ""
    for i, chunk_path in enumerate(chunk_paths):
        print(f"Transcrevendo parte {i+1}/{len(chunk_paths)}...")
        chunk_transcript = transcribe_audio(chunk_path, language)
        full_transcript += f"\n\n[Minuto {i} - {i+1}]\n{chunk_transcript}"
        os.remove(chunk_path)  # Remove o chunk temporário
    return full_transcript
