import time
from typing import List, Dict, Any
from duckduckgo_search import DDGS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolicyDiscoverer:
    def __init__(self):
        self.ddgs = DDGS()

    def discover(self, country: str, issue: str, year: str) -> List[Dict[str, Any]]:
        """
        Discovers potentially relevant policy documents using web search.
        Does not use AI models.
        """
        results = []
        query = f"{country} {issue} policy {year}"
        logger.info(f"Searching: {query}")
        
        try:
            # We fetch a conservative number of results to avoid rate limiting
            search_results = self.ddgs.text(query, max_results=10)
            
            if search_results:
                for res in search_results:
                    results.append({
                        "title": res.get("title", ""),
                        "url": res.get("href", ""),
                        "source": "Web Search", # Could also extract domain name here
                        "country": country,
                        "issue": issue,
                        "date": year # Approximate date based on query
                    })
            time.sleep(1.5)  # Rate limiting delay
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            
        return results

    def discover_all(self, countries: List[str], issues: List[str], start_year: int, end_year: int) -> List[Dict[str, Any]]:
        all_results = []
        for country in countries:
            for issue in issues:
                for year in range(start_year, end_year + 1):
                    results = self.discover(country, issue, str(year))
                    all_results.extend(results)
        return all_results
