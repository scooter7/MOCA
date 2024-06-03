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

# Function to summarize content to fit within token limits
def summarize_text(text, model="gpt-3.5-turbo", max_tokens=3000):
    messages = [
        {"role": "system", "content": "You are a summarizer."},
        {"role": "user", "content": f"Please summarize the following text:\n{text}"}
    ]
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens
    )
    return response.choices[0].message['content'].strip()

# Function to use OpenAI to create a cohesive report
def create_report_with_openai(template_text, notes_text):
    # Check if the combined length of template and notes exceeds the token limit
    if len(template_text.split()) + len(notes_text.split()) > 8000:
        template_text = summarize_text(template_text)
        notes_text = summarize_text(notes_text)

    prompt = (
        f"Template:\n{template_text}\n\n"
        f"Notes:\n{notes_text}\n\n"
        "Please generate a cohesive report by placing the notes into the appropriate sections of the template and adding any necessary additional language."
    )
    
    messages = [
        {"role": "system", "content": "You are an assistant that helps generate cohesive reports by placing notes into the appropriate sections of the template and adding any necessary additional language."},
        {"role": "user", "content": prompt}
    ]
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",  # Use the appropriate model
        messages=messages,
        max_tokens=3000  # Adjust max_tokens based on your needs
    )
    return response.choices[0].message['content'].strip()

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
