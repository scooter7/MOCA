import streamlit as st
import re
from PyPDF2 import PdfReader
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Function to extract text from PDF incrementally
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = []
    for page in pdf_reader.pages:
        text.append(page.extract_text())
    return "\n".join(text)

# Function to identify sections in the template
def identify_sections(template_text):
    headers = re.findall(r'([A-Z ]+)\n', template_text)
    return headers

# Function to match notes to sections
def match_notes_to_sections(headers, notes_text):
    sections = {header: "" for header in headers}
    current_header = None

    for line in notes_text.split("\n"):
        header_match = re.match(r'([A-Z ]+)', line)
        if header_match and header_match.group(1) in headers:
            current_header = header_match.group(1)
        elif current_header:
            sections[current_header] += line + "\n"
    
    return sections

# Function to merge notes into the template
def merge_notes_into_template(template_text, notes_sections):
    merged_text = template_text
    for header, notes in notes_sections.items():
        merged_text = merged_text.replace(header, header + "\n" + notes)
    return merged_text

# Function to create a downloadable PDF
def create_pdf(text):
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=letter)
    width, height = letter

    lines = text.split("\n")
    for line in lines:
        c.drawString(72, height - 72, line)
        height -= 15
        if height < 72:  # Create new page if the current page is filled
            c.showPage()
            height = letter[1] - 72

    c.save()
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
        
        headers = identify_sections(template_text)
        notes_sections = match_notes_to_sections(headers, notes_text)

        if st.button("Generate Report"):
            merged_text = merge_notes_into_template(template_text, notes_sections)
            pdf_output = create_pdf(merged_text)
            
            st.download_button(
                label="Download Report",
                data=pdf_output,
                file_name="generated_report.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"An error occurred: {e}")

