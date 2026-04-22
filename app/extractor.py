import os
import json
import re
import google.generativeai as genai
from app.pdf_utils import extract_text_from_pdf

_model = None

def get_model():
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY is not set. Please add your key to the .env file.")
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-2.5-flash")
    return _model


EXTRACTION_PROMPT = """You are a document analysis assistant. Analyze the following PDF text and return a JSON object.

Your job:
1. Detect the document type (e.g. Invoice, Resume/CV, Financial Report, Medical Report, Legal Contract, Research Paper, or Other)
2. Extract relevant structured fields based on the document type
3. Write a clear plain-English summary (3-5 sentences)

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "document_type": "<type>",
  "summary": "<plain English summary>",
  "fields": {{
    "<field_name>": "<value>",
    ...
  }},
  "confidence": "high" | "medium" | "low"
}}

Field extraction rules by document type:
- Invoice: invoice_number, date, vendor, buyer, total_amount, currency, due_date, line_items_count
- Resume/CV: candidate_name, email, phone, location, current_role, years_experience, top_skills, education
- Financial Report: company, period, revenue, net_profit, total_assets, currency, report_type
- Medical Report: patient_name, date, doctor, diagnosis, medications, follow_up
- Legal Contract: parties_involved, contract_type, effective_date, expiry_date, key_obligations
- Research Paper: title, authors, journal, year, abstract_summary, key_findings
- Other: extract whatever structured fields you can identify (at least 5)

If a field is not found, use null as the value.

PDF TEXT:
{text}
"""


async def extract_and_summarize(file_path: str, filename: str) -> dict:
    # Step 1: Extract raw text
    try:
        raw_text = extract_text_from_pdf(file_path)
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "filename": filename
        }

    # Truncate to avoid token limits (Gemini Flash handles ~30k tokens)
    truncated_text = raw_text[:12000]

    # Step 2: Call Gemini
    try:
        prompt = EXTRACTION_PROMPT.format(text=truncated_text)
        response = get_model().generate_content(prompt)
        raw_response = response.text.strip()

        # Strip markdown code fences if present
        raw_response = re.sub(r"^```json\s*", "", raw_response)
        raw_response = re.sub(r"\s*```$", "", raw_response)

        parsed = json.loads(raw_response)

        return {
            "success": True,
            "filename": filename,
            "document_type": parsed.get("document_type", "Unknown"),
            "summary": parsed.get("summary", ""),
            "fields": parsed.get("fields", {}),
            "confidence": parsed.get("confidence", "medium"),
            "pages_processed": raw_text.count("\n\n") + 1
        }

    except json.JSONDecodeError:
        # Gemini returned something unparseable — try to salvage the text
        return {
            "success": True,
            "filename": filename,
            "document_type": "Unknown",
            "summary": raw_response[:500] if raw_response else "Could not generate summary.",
            "fields": {},
            "confidence": "low",
            "pages_processed": raw_text.count("\n\n") + 1
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Gemini API error: {str(e)}",
            "filename": filename
        }
