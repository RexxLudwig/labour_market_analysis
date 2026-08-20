import json
import logging
import re
from typing import Dict, Any, List
import ollama
from src.models.schemas import VerificationResult

logger = logging.getLogger(__name__)

class PolicyVerifier:
    def __init__(self, model: str = "phi3:mini"):
        # Can use phi3:mini for quick checks or gemma3:4b
        self.model = model
        
        # Rule-based heuristics
        self.proposal_keywords = ["proposed", "draft", "considering", "may introduce", "bill", "planning to"]
        self.enacted_keywords = ["entered into force", "effective from", "gazetted", "enacted", "passed", "law"]
        
    def _rule_based_check(self, extracted_status: str, original_text: str) -> List[str]:
        """
        Executes deterministic checks. E.g., verifying if the extracted status 
        conflicts with the keywords heavily present in the text.
        """
        issues = []
        text_lower = original_text.lower()
        status_lower = extracted_status.lower() if extracted_status else ""
        
        # Check if the LLM claims it's enacted
        is_claimed_enacted = "enact" in status_lower or "force" in status_lower
        
        if is_claimed_enacted:
            has_proposal_words = any(k in text_lower for k in self.proposal_keywords)
            has_enacted_words = any(k in text_lower for k in self.enacted_keywords)
            
            if has_proposal_words and not has_enacted_words:
                issues.append(
                    "Rule Warning: Extracted status is 'Enacted', but the source text "
                    "heavily uses proposal/draft language without enacted language."
                )
                
        return issues
        
    def verify(self, extracted_data: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """
        Hybrid verification: combining deterministic rules with LLM fact-checking.
        """
        # 1. Run deterministic rules
        rule_issues = self._rule_based_check(extracted_data.get("status", ""), original_text)
        
        # 2. Ask LLM to cross-check the details
        prompt = f"""
You are an expert fact-checker. 
Compare the extracted policy information below against the original source text.
Check for hallucinations, specifically around policy status (enacted vs proposed), dates, and key provisions.

Extracted Data:
{json.dumps(extracted_data, indent=2)}

Original Text Snippet:
{original_text[:8000]}

Respond ONLY with valid JSON in the following format:
{{
  "verified": true or false,
  "confidence": "HIGH", "MEDIUM", or "LOW",
  "issues": ["Issue description 1", "Issue description 2"] // Empty list if verified=true
}}
"""
        try:
            response = ollama.chat(
                model=self.model, 
                messages=[{"role": "user", "content": prompt}], 
                format="json", 
                options={"temperature": 0.0} 
            )
            
            result_text = response['message']['content']
            result_json = json.loads(result_text)
            
            # Combine rule-based issues with LLM-identified issues
            if rule_issues:
                result_json["issues"] = rule_issues + result_json.get("issues", [])
                result_json["verified"] = False
                # If rules flagged an issue, we downgrade confidence to LOW
                result_json["confidence"] = "LOW"
                
            validated_result = VerificationResult(**result_json)
            return validated_result.model_dump()
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {"verified": False, "confidence": "LOW", "issues": ["System error during verification."]}
