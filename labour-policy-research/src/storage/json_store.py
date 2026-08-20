import json
import os
import uuid
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class JSONStore:
    def __init__(self, file_path: str = "data/policies.json"):
        self.file_path = file_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)
        
    def _generate_id(self, policy: Dict[str, Any]) -> str:
        """
        Generates a human-readable slug ID (e.g. vn-employment-law-2025-a1b2)
        """
        country = policy.get("country", "unknown").lower()
        title = policy.get("policy_title", "untitled").lower()
        
        # Grab the first few words to create a readable slug
        title_slug = "-".join(title.split()[:5]) 
        # Remove special characters from slug
        title_slug = re.sub(r'[^a-z0-9\-]', '', title_slug)
        
        return f"{country}-{title_slug}-{str(uuid.uuid4())[:8]}"
        
    def save_policies(self, policies: List[Dict[str, Any]]):
        """
        Saves a list of policies to the JSON file.
        Generates IDs for new policies.
        """
        existing_data = self.load_policies()
        
        for policy in policies:
            if "id" not in policy:
                policy["id"] = self._generate_id(policy)
            
            existing_data.append(policy)
            
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(policies)} policies to {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to save policies to JSON: {e}")
            
    def load_policies(self) -> List[Dict[str, Any]]:
        """Loads all policies from the JSON file."""
        if not os.path.exists(self.file_path):
            return []
            
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            logger.warning(f"File {self.file_path} is empty or corrupted. Returning empty list.")
            return []
        except Exception as e:
            logger.error(f"Failed to load policies: {e}")
            return []
