import requests
import fitz  # PyMuPDF
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

def fetch_pdf(url: str, timeout: int = 15) -> bytes:
    """Fetches PDF content from a URL as raw bytes."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Failed to fetch PDF from {url}: {e}")
        return b""

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text from raw PDF bytes."""
    if not pdf_bytes:
        return ""
        
    text = ""
    temp_file_path = None
    try:
        # PyMuPDF opens from file path best, so we use a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name

        doc = fitz.open(temp_file_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
    return text
