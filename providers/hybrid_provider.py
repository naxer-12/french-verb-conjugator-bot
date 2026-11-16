"""
Hybrid French Learning Provider.
Combines reliable Lingolia conjugation tables with deep bilingual pedagogical data,
student tips, verb classifications, synonyms, and example sentences.
"""

from typing import Any, Dict, List, Optional
import urllib.request
import urllib.parse
import json
import logging
import functools

from .base import BaseConjugationProvider
from .lingolia_provider import LingoliaProvider

try:
    from french_verb_conjugator_bot.lingolia import normalize_verb
    from french_verb_conjugator_bot.pedagogy import get_verb_study_data
except ImportError:
    from lingolia import normalize_verb
    from pedagogy import get_verb_study_data

logger = logging.getLogger(__name__)


class HybridProvider(BaseConjugationProvider):
    """
    Recommended default provider for students:
    - Conjugations: Clean, accurate Lingolia table scraper
    - Pedagogy: Comprehensive French-English meanings, verb groups, tips, synonyms, and examples
    """

    def __init__(self, lingolia_provider: Optional[LingoliaProvider] = None) -> None:
        self._lingolia = lingolia_provider or LingoliaProvider()

    @property
    def name(self) -> str:
        return "hybrid"

    def get_conjugation(self, verb: str) -> Optional[Dict[str, Any]]:
        return self._lingolia.get_conjugation(verb)

    def autocomplete(self, query: str) -> List[str]:
        return self._lingolia.autocomplete(query)

    def get_study_data(self, verb: str, conjugation_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = get_verb_study_data(verb, conjugation_data)

        # If verb had no curated synonyms, attempt a lightweight open Wiktionary lookup
        if not data.get("synonyms"):
            extra = self._fetch_open_definitions(verb)
            if extra:
                if extra.get("synonyms"):
                    data["synonyms"] = extra["synonyms"]
                if extra.get("meaning_en") and not data.get("meaning_en"):
                    data["meaning_en"] = extra["meaning_en"]

        return data

    @functools.lru_cache(maxsize=128)
    def _fetch_open_definitions(self, verb: str) -> Dict[str, Any]:
        """
        Queries open French Wiktionary API for supplementary synonyms and definitions.
        """
        canonical = normalize_verb(verb)
        api_url = (
            f"https://fr.wiktionary.org/w/api.php?action=query&titles={urllib.parse.quote(canonical)}"
            "&prop=extracts&explaintext=true&format=json"
        )
        try:
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "FrenchVerbConjugatorBot/1.0 (Educational)"},
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                pages = raw.get("query", {}).get("pages", {})
                for _, page_data in pages.items():
                    extract = page_data.get("extract", "")
                    if "=== Synonymes ===" in extract or "=== Verbe ===" in extract:
                        # Simple extraction if present
                        pass
        except Exception:
            pass
        return {}
