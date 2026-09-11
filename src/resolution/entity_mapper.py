import re
import logging
from rapidfuzz import process, fuzz
from typing import Tuple

logger = logging.getLogger(__name__)

class EntityResolver:
    """
    Phase IV: Deterministic Entity Resolution.
    Canonicalizes Startup and Product names using fuzzy lexical distance and string normalization.
    """
    def __init__(self):
        # Mock database of canonical AI startups as requested by the assignment
        self.canonical_entities = [
            "OpenAI", "Anthropic", "DeepMind", "Hugging Face", "Mistral AI",
            "Cohere", "Scale AI", "Databricks", "Midjourney", "Stability AI",
            "Perplexity", "Glean", "Runway", "Inflection AI", "Adept"
        ]
        self.threshold = 85.0 # Minimum RapidFuzz match score to map to an existing entity

    def _normalize_string(self, name: str) -> str:
        """Removes common corporate suffixes and normalizes whitespace/case."""
        name = name.lower().strip()
        
        # Remove punctuation
        name = re.sub(r'[^\w\s]', '', name)
        
        # Remove common corporate suffixes
        suffixes = r'\b(inc|corp|corporation|llc|ltd|company)\b'
        name = re.sub(suffixes, '', name).strip()
        
        # Collapse multiple spaces
        name = re.sub(r'\s+', ' ', name)
        return name

    def resolve(self, raw_name: str) -> Tuple[str, bool, float]:
        """
        Attempts to map a raw extracted name to a canonical entity.
        Returns: (Resolved_Name, Is_Mapped, Confidence_Score)
        """
        normalized_raw = self._normalize_string(raw_name)
        
        # Create a lookup mapping of normalized canonical -> real canonical
        normalized_db = {self._normalize_string(c): c for c in self.canonical_entities}
        
        # Use RapidFuzz to find the closest lexical match
        # fuzz.WRatio handles partial matches, different ordering, and casing gracefully
        match = process.extractOne(
            normalized_raw, 
            list(normalized_db.keys()), 
            scorer=fuzz.WRatio
        )

        if match:
            best_match_normalized, score, _ = match
            if score >= self.threshold:
                canonical_name = normalized_db[best_match_normalized]
                return canonical_name, True, score
        
        # If no match exceeds the threshold, treat it as a new distinct entity
        return raw_name, False, 0.0

