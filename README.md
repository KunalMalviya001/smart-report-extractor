# Smart Report Extractor

A FastAPI service that accepts a PDF and returns structured extracted fields + a plain-English summary, powered by **Gemini 2.5 Flash**.

---

## What It Does

- Accepts any PDF upload via a web UI or `POST /extract`
- Detects the document type automatically (Invoice, CV, Financial Report, Medical Report, Legal Contract, Research Paper, Other)
- Extracts typed fields relevant to that document type
- Returns a plain-English summary of the document
- Handles bad input and extraction failures gracefully

## Supported Document Types

| Type | Extracted Fields |
|------|-----------------|
| Invoice | invoice_number, date, vendor, buyer, total_amount, currency, due_date |
| Resume/CV | candidate_name, email, phone, location, current_role, top_skills, education |
| Financial Report | company, period, revenue, net_profit, total_assets, currency |
| Medical Report | patient_name, date, doctor, diagnosis, medications, follow_up |
| Legal Contract | parties_involved, contract_type, effective_date, expiry_date |
| Research Paper | title, authors, journal, year, key_findings |
| Other | Any 5+ fields the model can identify |

---

## Setup & Run

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd smart-report-extractor
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your Gemini API key

```bash
cp .env.example .env
# Edit .env and add your key:
# GEMINI_API_KEY=your_key_here
```

Get a free API key at [https://aistudio.google.com](https://aistudio.google.com)

### 5. Run the server

```bash
python run.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## API

### `POST /extract`

**Request:** `multipart/form-data` with a `file` field (PDF only)

**Response:**

```json
{
  "success": true,
  "filename": "invoice_q3.pdf",
  "document_type": "Invoice",
  "summary": "This is a Q3 2024 invoice from Acme Corp...",
  "fields": {
    "invoice_number": "INV-2024-0391",
    "vendor": "Acme Corp",
    "total_amount": "$4,200.00",
    "due_date": "2024-10-15"
  },
  "confidence": "high"
}
```

---

## Project Structure

```
smart-report-extractor/
├── app/
│   ├── main.py          # FastAPI app + routes
│   ├── extractor.py     # Gemini API call + response parsing
│   └── pdf_utils.py     # PDF text extraction (pdfplumber)
├── templates/
│   └── index.html       # Web UI (single file, no build step)
├── uploads/             # Temp storage (files deleted after processing)
├── requirements.txt
├── .env.example
├── REFLECTION.md
└── README.md
```

---

## Design Decisions

**Why pdfplumber?** It's the most reliable Python library for extracting structured text from PDFs, handles multi-page docs well, and has no external dependencies.

**Why Gemini 2.5 Flash?** Fast, cost-effective, and has a large enough context window (1M tokens) that even long PDFs don't need chunking in most cases. 2.5 Flash improves on 1.5 with better reasoning and more accurate structured extraction.

**Why a single LLM call?** One prompt does both detection and extraction. This is simpler, faster, and avoids the "telephone game" problem where a second LLM call interprets the first one's output. The tradeoff is that a bad detection leads to wrong fields — mitigated by asking the model to fall back to "Other" and extract whatever it can.

**If the LLM is unavailable:** The `pdf_utils.py` layer is completely independent. The raw text extraction still works. A fallback could run regex-based extraction for known formats (e.g., invoices often have consistent patterns) — this is noted in the code as a future improvement.
