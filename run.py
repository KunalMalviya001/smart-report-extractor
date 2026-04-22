"""
Entry point — run with: python run.py
Or directly: uvicorn app.main:app --reload
"""
import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
