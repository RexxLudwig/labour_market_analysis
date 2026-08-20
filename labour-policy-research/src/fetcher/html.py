import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def fetch_html(url: str, timeout: int = 10) -> str:
    """Fetches HTML content from a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch HTML from {url}: {e}")
        return ""

def extract_text_from_html(html_content: str) -> str:
    """Extracts main text content from HTML, stripping boilerplate."""
    if not html_content:
        return ""
        
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements like scripts, styles, navs, footers, etc.
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
            element.decompose()
            
        text = soup.get_text(separator='\n')
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from HTML: {e}")
        return ""
