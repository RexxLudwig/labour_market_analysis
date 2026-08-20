import os
import yaml
import logging
from typing import List, Dict, Any

from src.discovery.search import PolicyDiscoverer
from src.fetcher.html import fetch_html, extract_text_from_html
from src.fetcher.pdf import fetch_pdf, extract_text_from_pdf
from src.processing.cleaner import clean_text
from src.processing.relevance import RelevanceFilter
from src.processing.extraction import PolicyExtractor
from src.processing.verification import PolicyVerifier
from src.processing.deduplication import PolicyDeduplicator
from src.storage.json_store import JSONStore
from src.report.pdf_generator import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(file_path: str) -> Any:
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def run_pipeline():
    logger.info("Starting Labour Market Policy Research System Pipeline")
    
    # 1. Load Configurations
    countries_conf = load_config("config/countries.yaml")
    issues_conf = load_config("config/issues.yaml")
    settings_conf = load_config("config/settings.yaml")
    
    countries = countries_conf.get("countries", [])
    issues = issues_conf.get("issues", [])
    start_year = int(settings_conf.get("date_range", {}).get("from", "2024").split("-")[0])
    end_year = int(settings_conf.get("date_range", {}).get("to", "2026").split("-")[0])
    
    # Initialize components
    discoverer = PolicyDiscoverer()
    relevance_filter = RelevanceFilter(model="phi3:mini")
    extractor = PolicyExtractor(model="gemma3:4b")
    verifier = PolicyVerifier(model="phi3:mini")
    deduplicator = PolicyDeduplicator(embed_model="nomic-embed-text")
    store = JSONStore()
    pdf_generator = ReportGenerator()
    
    extracted_policies = []
    
    # 2. Web Search
    logger.info(f"Discovering policies for {len(countries)} countries across {len(issues)} issues...")
    search_results = discoverer.discover_all(countries, issues, start_year, end_year)
    logger.info(f"Discovered {len(search_results)} potential documents.")
    
    # Pipeline per document
    for idx, result in enumerate(search_results, 1):
        url = result['url']
        country = result['country']
        issue = result['issue']
        
        logger.info(f"[{idx}/{len(search_results)}] Processing URL: {url}")
        
        # 3. Document Fetcher
        is_pdf = url.lower().endswith(".pdf")
        if is_pdf:
            raw_content = fetch_pdf(url)
            raw_text = extract_text_from_pdf(raw_content)
        else:
            raw_content = fetch_html(url)
            raw_text = extract_text_from_html(raw_content)
            
        if not raw_text.strip():
            logger.warning("Could not extract text. Skipping.")
            continue
            
        # 4. Text Cleaning
        clean_doc_text = clean_text(raw_text)
        snippet = clean_doc_text[:3000] # Provide a chunk for relevance
        
        # 5. Relevance Classification (Ollama)
        relevance = relevance_filter.check_relevance(result['title'], snippet, issue)
        if not relevance.get("relevant"):
            logger.info("Document not relevant. Skipping.")
            continue
            
        # 6. Policy Extraction (Ollama)
        logger.info("Document relevant. Extracting policy details...")
        extracted_data = extractor.extract_details(clean_doc_text, country, issue)
        
        if not extracted_data:
            logger.warning("Failed to extract structured data. Skipping.")
            continue
            
        # Add metadata for deduplication and source linking
        extracted_data["source_url"] = url
        
        # 7. Verification
        logger.info("Verifying extraction against source...")
        verification = verifier.verify(extracted_data, clean_doc_text)
        
        # We append verification results to the policy record
        extracted_data["verified"] = verification.get("verified", False)
        extracted_data["confidence"] = verification.get("confidence", "LOW")
        extracted_data["verification_issues"] = verification.get("issues", [])
        
        extracted_policies.append(extracted_data)
        
    logger.info(f"Successfully processed and extracted {len(extracted_policies)} relevant policies.")
    
    # 8. Deduplication
    if not extracted_policies:
        logger.info("No policies found. Exiting.")
        return
        
    logger.info("Running deduplication...")
    deduped_policies = deduplicator.deduplicate(extracted_policies)
    logger.info(f"Deduplication complete. {len(deduped_policies)} unique policies identified.")
    
    # 9. Store to policies.json
    logger.info("Saving to JSON store...")
    store.save_policies(deduped_policies)
    
    # 10. Generate PDF
    logger.info("Generating Final PDF Report...")
    pdf_generator.generate(deduped_policies)
    logger.info("Pipeline execution finished successfully.")

if __name__ == "__main__":
    run_pipeline()
