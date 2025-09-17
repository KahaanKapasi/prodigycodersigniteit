# verify_report.py
import fitz  # PyMuPDF
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))  # store API key in env
model = genai.GenerativeModel("gemini-1.5-flash")

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def verify_medical_report(pdf_path):
    """Return True if donor is eligible, False otherwise."""
    report_text = extract_text_from_pdf(pdf_path)

    prompt = f"""
    You are a medical eligibility checker for blood donation.
    Rules:
    - Hemoglobin must be >= 12.5
    - Age between 18 and 65
    - No serious medical conditions like HIV, Hepatitis, Cancer, TB, etc.
    Based on the following report, respond only with 'YES' (eligible) or 'NO' (not eligible).

    Report:
    {report_text}
    """

    response = model.generate_content(prompt)
    result = response.text.strip().upper()

    return result == "YES"
