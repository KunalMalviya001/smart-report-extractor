"""
Entry point — run with: python run.py
Or directly: uvicorn app.main:app --reload
"""
import uvicorn
from dotenv import load_dotenv
import os


load_dotenv()

if __name__ == "__main__":
    uvicorn.run("app.main:app", port= int(os.getenv("PORT")) , reload=True)
