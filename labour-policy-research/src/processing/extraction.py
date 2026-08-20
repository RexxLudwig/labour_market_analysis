import json
import logging
from typing import Dict, Any
import ollama
from src.models.schemas import PolicyExtractionResult

logger = logging.getLogger(__name__)

class PolicyExtractor:
    def __init__(self, model: str = "gemma3:4b"):
        # Using gemma3:4b as default as suggested for better structured extraction
        self.model = model
        
    def extract_details(self, document_text: str, country: str, issue: str) -> Dict[str, Any]:
        """
        Reads the policy document and extracts specific structured information 
        using a local Ollama LLM.
        """
        # Truncate text slightly if necessary to fit in standard context windows,
        # though gemma3 handles 8k well.
        text_snippet = document_text[:12000] 
        
        prompt = f"""
You are an expert labour market policy analyst. 
Read the following policy document from {country} concerning {issue}.
Extract the required information and respond ONLY with valid JSON matching the exact structure requested.
Do not include any markdown formatting or explanations outside of the JSON block.

Document:
{text_snippet}

Extract the following JSON structure:
{{
  "country": "{country}",
  "policy_title": "Full title of the policy",
  "policy_type": "Act/Decree/Regulation/Guideline etc.",
  "status": "Enacted/Proposed/Draft etc.",
  "announcement_date": "YYYY-MM-DD or Unknown",
  "effective_date": "YYYY-MM-DD or Unknown",
  "target_groups": ["group1", "group2"],
  "policy_objective": "Main objective...",
  "key_provisions": ["provision1", "provision2"],
  "implementation_agency": "Agency Name",
  "labour_market_issue": "{issue}"
}}
"""
        try:
            response = ollama.chat(
                model=self.model, 
                messages=[{"role": "user", "content": prompt}], 
                format="json", 
                # Request a larger context window just in case
                options={"temperature": 0.0, "num_ctx": 16000} 
            )
            
            result_text = response['message']['content']
            result_json = json.loads(result_text)
            
            # Validate output structure using Pydantic
            validated_result = PolicyExtractionResult(**result_json)
            return validated_result.model_dump()
            
        except Exception as e:
            logger.error(f"Failed to extract policy details: {e}")
            return {}
