import streamlit as st
import re
import pdfplumber
import openai
from io import BytesIO
from fpdf import FPDF

# Set up OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

# Function to extract text from PDF using pdfplumber
def extract_text_from_pdf(uploaded_file):
    text = []
    with pdfplumber.open(BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text())
    return "\n".join(text)

# Function to split text into chunks
def split_text_into_chunks(text, max_tokens=2048):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1  # +1 for the space
        if current_length + word_length > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(word)
        current_length += word_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Function to use OpenAI to process each chunk and generate report
def create_report_with_openai(template_text, notes_text, max_tokens=2048):
    template_chunks = split_text_into_chunks(template_text, max_tokens)
    notes_chunks = split_text_into_chunks(notes_text, max_tokens)

    reports = []

    for template_chunk, notes_chunk in zip(template_chunks, notes_chunks):
        prompt = (
            f"Template:\n{template_chunk}\n\n"
            f"Notes:\n{notes_chunk}\n\n"
            "Please generate a cohesive report by placing the notes into the appropriate sections of the template and adding any necessary additional language."
        )
        
        messages = [
            {"role": "system", "content": "You are an assistant that helps generate cohesive reports by placing notes into the appropriate sections of the template and adding any necessary additional language."},
            {"role": "user", "content": prompt}
        ]
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Use the appropriate model
            messages=messages,
            max_tokens=max_tokens
        )
        reports.append(response.choices[0].message.content.strip())

    return "\n\n".join(reports)

# Function to create a downloadable PDF using fpdf
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Generated Report', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body.encode('latin-1', 'replace').decode('latin-1'))
        self.ln()

def create_pdf(text):
    pdf = PDF()
    pdf.add_page()
    for line in text.split("\n"):
        if line.strip() == "":
            continue
        if line.isupper():
            pdf.chapter_title(line)
        else:
            pdf.chapter_body(line)
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# Streamlit app layout
st.title("Report Generator")
st.write("Upload the template report format and report notes files.")

# File upload
template_file = st.file_uploader("Upload Template Report Format (PDF)", type="pdf")
notes_file = st.file_uploader("Upload Report Notes (PDF)", type="pdf")

if template_file and notes_file:
    try:
        template_text = extract_text_from_pdf(template_file)
        notes_text = extract_text_from_pdf(notes_file)

        if st.button("Generate Report"):
            report_text = create_report_with_openai(template_text, notes_text)
            pdf_output = create_pdf(report_text)
            
            st.download_button(
                label="Download Report",
                data=pdf_output,
                file_name="generated_report.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"An error occurred: {e}")
