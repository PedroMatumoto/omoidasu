import openai
from dotenv import find_dotenv, load_dotenv

_ = load_dotenv(find_dotenv())

client = openai.OpenAI()


def get_meeting_title(transcription):
    """
    Get the meeting title from the transcription.
    Args:
        transcription: Transcription text.
    Returns:
        Meeting title.
    """
    prompt = (
        f"Extract the meeting title from the following transcription:\n{transcription}"
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content


def save_text_file(file_path, text):
    """
    Save the tedxt string to a file.
    Args:
        file_path: Path to the file where the text will be saved.
        text: Text to be saved.
    """
    with open(file_path, "w") as f:
        f.write(text)


def read_text_file(file_path):
    """
    Read the text from a file.
    Args:
        file_path: Path to the file to be read.
    Returns:
        Text read from the file.
    """
    if not file_path.exists():
        return ""
    with open(file_path, "r") as f:
        return f.read()
