import json
import logging
from typing import Dict, Any
import ollama
from src.models.schemas import RelevanceResult

logger = logging.getLogger(__name__)

class RelevanceFilter:
    def __init__(self, model: str = "phi3:mini"):
        # We can use small models like phi3:mini or gemma3:4b for simple classification
        self.model = model
        
    def check_relevance(self, title: str, text_snippet: str, target_issue: str) -> Dict[str, Any]:
        """
        Uses a local Ollama model to classify if a document is relevant to the target issue.
        Returns a dictionary indicating relevance.
        """
        prompt = f"""
You are an expert labour market policy analyst. 
Determine if the following document is relevant to the labour market issue: "{target_issue}".

Title: {title}
Snippet: {text_snippet}

Respond ONLY with valid JSON in the following format.
If relevant: {{"relevant": true, "issue": "{target_issue}", "reason": "short explanation"}}
If not relevant: {{"relevant": false}}
"""
        try:
            # We enforce JSON output directly from Ollama
            response = ollama.chat(
                model=self.model, 
                messages=[{"role": "user", "content": prompt}], 
                format="json", 
                options={"temperature": 0.0}
            )
            
            result_text = response['message']['content']
            result_json = json.loads(result_text)
            
            # Validate output structure using Pydantic
            validated_result = RelevanceResult(**result_json)
            return validated_result.model_dump(exclude_none=True)
            
        except Exception as e:
            logger.error(f"Failed to check relevance for '{title}': {e}")
            # Fail closed - assume not relevant on error
            return {"relevant": false}
