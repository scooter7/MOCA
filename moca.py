import streamlit as st
import re
import pdfplumber
from io import BytesIO
from fpdf import FPDF

# Function to extract text from PDF using pdfplumber
def extract_text_from_pdf(uploaded_file):
    text = []
    with pdfplumber.open(BytesIO(uploaded_file.read())) as pdf:
        for page in pdf.pages:
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
