from fpdf import FPDF
import openai
from dotenv import find_dotenv, load_dotenv
import streamlit as st
import shutil

_ = load_dotenv(find_dotenv())

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def generate_pdf(title, meeting_date, abstract, transcription, output_path):
    """
    Generate a PDF file with the meeting information.
    Args:
        title: Meeting title.
        meeting_date: Meeting date.
        abstract: Meeting abstract.
        transcription: Meeting transcription.
        output_path: Path to save the generated PDF.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 10, f"Meeting Title: {title}", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Meeting Date: {meeting_date}", ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(0, 10, "Abstract:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, abstract)
    pdf.ln(10)

    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(0, 10, "Transcription:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, transcription)

    pdf.output(output_path)


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


def generate_abstract(file_path, transcription):
    """
    Generate an abstract from the transcription file.
    Args:
        file_path: Path to the transcription file.
    Returns:
        Abstract text.
    """
    prompt = f"""Make an abstract of the text delimite by triple quotes:\n\"\"\"\n{transcription}\n\"\"\"\n
    This text is a transcription of a meeting. The abstract should be a summary of the main points discussed in the meeting.
    It should be concise and to the point, highlighting the key takeaways and conclusions drawn during the meeting.
    The abstract should be no more than 300 words long and be written in a formal tone. In the end, provide a list of action items and decisions made during the meeting, in bullet points.
    You must not create any new information, only summarize the text.
    The final format should be:
    - write the abstract here
    **Action items:**
    - write the action items here
    **Decisions:** 
    - write the decisions here


    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    save_text_file(file_path / "abstract.txt", response.choices[0].message.content)


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
        text = f.read()
        f.close()
        return text


def delete_all_files(dir_meeting):
    """
    Delete all files in the meeting directory.
    Args:
        dir_meeting: Path to the meeting directory.
    """
    for item in dir_meeting.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
