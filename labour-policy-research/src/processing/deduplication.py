import ollama
import numpy as np
from typing import List, Dict, Any
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)

class PolicyDeduplicator:
    def __init__(self, embed_model: str = "nomic-embed-text", similarity_threshold: float = 0.85):
        # We use a fast local embedding model for similarity comparisons
        self.embed_model = embed_model
        self.similarity_threshold = similarity_threshold

    def get_embedding(self, text: str) -> List[float]:
        try:
            response = ollama.embeddings(model=self.embed_model, prompt=text)
            return response['embedding']
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return []

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return np.dot(v1, v2) / (norm1 * norm2)

    def normalize_string(self, text: str) -> str:
        return text.lower().strip()

    def is_duplicate(self, policy1: Dict[str, Any], policy2: Dict[str, Any]) -> bool:
        # 1. Must be the same country
        if policy1.get("country") != policy2.get("country"):
            return False
            
        t1 = self.normalize_string(policy1.get("policy_title", ""))
        t2 = self.normalize_string(policy2.get("policy_title", ""))
        
        # 2. Exact Title Match
        if t1 == t2 and t1 != "":
            return True
            
        # 3. Fast Normalized String Distance
        string_sim = SequenceMatcher(None, t1, t2).ratio()
        if string_sim > 0.90:
            return True
            
        # 4. Date mismatch heuristic (if years differ, likely different policies)
        d1 = str(policy1.get("effective_date", ""))[:4]
        d2 = str(policy2.get("effective_date", ""))[:4]
        if d1.isdigit() and d2.isdigit() and d1 != d2:
            return False
            
        # 5. Semantic Embedding Similarity of title + key provisions
        text1 = t1 + " " + " ".join(policy1.get("key_provisions", []))
        text2 = t2 + " " + " ".join(policy2.get("key_provisions", []))
        
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        
        sim = self.cosine_similarity(emb1, emb2)
        if sim >= self.similarity_threshold:
            return True
            
        return False

    def deduplicate(self, policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of extracted policies and groups duplicates, merging their sources.
        """
        unique_policies = []
        
        for policy in policies:
            is_dup = False
            for u_policy in unique_policies:
                if self.is_duplicate(policy, u_policy):
                    # It's a duplicate, so we append the new source to the existing unique policy
                    if "sources" not in u_policy:
                        u_policy["sources"] = [u_policy.get("source_url", "Unknown Origin")]
                        
                    incoming_source = policy.get("source_url", "Unknown Origin")
                    if incoming_source not in u_policy["sources"]:
                        u_policy["sources"].append(incoming_source)
                        
                    is_dup = True
                    break
                    
            if not is_dup:
                # Not a duplicate, initialize the sources list
                if "sources" not in policy:
                    policy["sources"] = [policy.get("source_url", "Unknown Origin")]
                unique_policies.append(policy)
                
        return unique_policies
