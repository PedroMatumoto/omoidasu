import openai
from dotenv import find_dotenv, load_dotenv

_ = load_dotenv(find_dotenv())

client = openai.OpenAI()


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
