# AI Reflection Log

> Required by the Logos Labs Engineering Assessment.  
> This documents where AI tools helped and where they fell short.

---

## Project Overview

**Smart Report Extractor** is a FastAPI web application that accepts uploaded PDF files and returns structured, machine-readable data extracted by Google's Gemini AI. It detects the document type (Invoice, CV, Financial Report, Medical Report, Legal Contract, Research Paper, or Other) and returns a JSON object with relevant fields, a plain-English summary, and a confidence score. The frontend is a single-page drag-and-drop interface served directly from the FastAPI app.

**Stack:** Python · FastAPI · pdfplumber · Google Gemini API (`gemini-2.5-flash`) · Vanilla HTML/CSS

---

## Where AI Helped

### 1. Gemini extraction prompt design
AI drafted the initial structured prompt with per-document-type field lists and the JSON output contract. The structure was solid — defining six document types with specific fields to extract for each was well-organised. The base prompt was kept with minor tightening (see issues below).

### 2. FastAPI boilerplate
AI scaffolded the FastAPI app with file upload via `python-multipart`, CORS middleware, UUID-based temp file naming, and a static HTML route. The separation of concerns — `main.py` for routing, `extractor.py` for AI logic, `pdf_utils.py` for PDF parsing — was a clean architectural suggestion that was kept as-is.

### 3. pdfplumber choice
AI recommended `pdfplumber` over alternatives like PyMuPDF or PyPDF2. `pdfplumber` handles multi-column layouts better and has a simpler API. This was a good call and was kept.

### 4. Frontend UI
AI generated the initial HTML/CSS drag-and-drop interface with file validation, live state feedback (file selected, loading spinner, results panel), and clean result rendering with a field table. The editorial/paper aesthetic was a deliberate design choice suited to a document-processing tool.

### 5. JSON fence stripping
AI correctly anticipated that Gemini would sometimes wrap JSON output in markdown code fences (` ```json ... ``` `) even when instructed not to, and included a regex strip step:
```python
raw_response = re.sub(r"^```json\s*", "", raw_response)
raw_response = re.sub(r"\s*```$", "", raw_response)
```

---

## Where AI Was Wrong or Incomplete

### 1. Module-level API key crash (critical)
The AI-generated `extractor.py` called `genai.configure()` and initialised `GenerativeModel` at **module import time**:
```python
# Original — crashes the whole app if the key is missing or invalid
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")
```
Using `os.environ["GEMINI_API_KEY"]` raises a `KeyError` if the variable is not set, killing the entire process. This caused a `500 Internal Server Error` on every request to `/` because Python raised before the route handler even ran.

**Fix:** Moved initialisation into a lazy `get_model()` function using `os.getenv()` (returns `None` instead of raising), which only runs on the first actual API call:
```python
_model = None

def get_model():
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY is not set.")
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-2.5-flash")
    return _model
```

### 2. Windows encoding bug (critical)
The AI-generated `main.py` opened the HTML template with:
```python
with open("templates/index.html") as f:
```
On Windows, Python defaults to the system's `cp1252` (charmap) encoding. The HTML file contained non-ASCII characters (em-dashes, curly quotes, arrows), causing:
```
UnicodeDecodeError: 'charmap' codec can't decode ... character maps to <undefined>
```
This produced a `500 Internal Server Error` on the root route (`GET /`), meaning the homepage never loaded.

**Fix:** Explicit UTF-8 encoding:
```python
with open("templates/index.html", encoding="utf-8") as f:
```

### 3. JSON parsing had no fallback
The original draft called `json.loads(response.text)` directly with no error handling for malformed responses. A `JSONDecodeError` would bubble up as a 500.

**Fix:** Added a `JSONDecodeError` catch that salvages the raw text as the summary and returns `confidence: low` instead of crashing.

### 4. No uploaded file cleanup
The original scaffold wrote uploaded PDFs to disk but had no cleanup. On high traffic, the `uploads/` directory would grow indefinitely.

**Fix:** Added a `finally:` block in the `/extract` route to always delete the temp file after processing:
```python
finally:
    if file_path.exists():
        os.remove(file_path)
```

### 5. Model version was outdated
The AI defaulted to `gemini-1.5-flash`. Updated to `gemini-2.5-flash` for better extraction accuracy and reasoning.

---

## Summary

AI tools provided a solid starting scaffold and saved significant time on boilerplate (FastAPI setup, prompt structure, frontend drag-and-drop). However, two critical bugs — the module-level API key crash and the Windows encoding issue — would have blocked the app from running entirely and required direct diagnosis and fixing.

The pattern was consistent: AI produced plausible-looking code that worked in the "happy path" but missed platform-specific edge cases (Windows encoding), Python semantics (`os.environ` vs `os.getenv`), and operational concerns (file cleanup, lazy initialisation). Every generated piece required review. Bugs were subtle — the app started successfully but crashed on the first real request, which only became visible by reading server logs.

AI accelerated development by roughly 60–70%. The remaining effort was identifying *why* something failed, not just that it did.
