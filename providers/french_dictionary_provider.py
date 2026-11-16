"""
FrenchDictionary.com Dedicated Conjugation & Examples Provider.
Directly scrapes https://www.frenchdictionary.com/ for a requested word:
- Examples: https://www.frenchdictionary.com/examples/<word>?lang=fr
- Translations: https://www.frenchdictionary.com/translate/<word>
- Conjugations: https://www.frenchdictionary.com/conjugate/<word>

Handles Cloudflare Turnstile 403 gracefully with direct links and pedagogical support.
"""

from typing import Any, Dict, List, Optional, Tuple
import urllib.parse
import logging

from .base import BaseConjugationProvider
from .hybrid_provider import HybridProvider

try:
    from french_verb_conjugator_bot.frenchdictionary_scraper import FrenchDictionaryScraper
    from french_verb_conjugator_bot.lingolia import normalize_verb
    from french_verb_conjugator_bot.pedagogy import get_verb_study_data
except ImportError:
    from frenchdictionary_scraper import FrenchDictionaryScraper
    from lingolia import normalize_verb
    from pedagogy import get_verb_study_data

logger = logging.getLogger(__name__)


class FrenchDictionaryProvider(BaseConjugationProvider):
    """
    Dedicated Provider for frenchdictionary.com.
    Directly scrapes word pages, example sentences, and translations.
    """

    def __init__(
        self,
        fallback_provider: Optional[BaseConjugationProvider] = None,
        scraper: Optional[FrenchDictionaryScraper] = None,
    ) -> None:
        self._fallback = fallback_provider or HybridProvider()
        self._scraper = scraper or FrenchDictionaryScraper()
        self._base_url = "https://www.frenchdictionary.com"

    @property
    def name(self) -> str:
        return "frenchdictionary"

    def fetch_word_examples(self, word: str) -> Tuple[bool, List[Tuple[str, str]], str]:
        """Directly scrapes https://www.frenchdictionary.com/examples/<word>?lang=fr."""
        return self._scraper.fetch_word_examples(word)

    def fetch_word_translation(self, word: str) -> Tuple[bool, Dict[str, Any], str]:
        """Directly scrapes https://www.frenchdictionary.com/translate/<word>."""
        return self._scraper.fetch_word_translation(word)

    def get_conjugation(self, verb: str) -> Optional[Dict[str, Any]]:
        norm = normalize_verb(verb)
        target_url = f"{self._base_url}/examples/{urllib.parse.quote(norm)}?lang=fr"
        conj_url = f"{self._base_url}/conjugate/{urllib.parse.quote(norm)}"

        # Attempt to scrape examples directly for this word
        success, scraped_examples, status_msg = self._scraper.fetch_word_examples(norm)

        # Delegate conjugation table assembly to fallback
        res = self._fallback.get_conjugation(verb)
        if res:
            res = res.copy()
            res["url"] = target_url
            res["examples_url"] = target_url
            res["conjugate_url"] = conj_url
            res["source"] = "FrenchDictionary.com"
            if success and scraped_examples:
                res["scraped_examples"] = scraped_examples
            else:
                res["cf_status"] = status_msg
        return res

    def autocomplete(self, query: str) -> List[str]:
        return self._fallback.autocomplete(query)

    def get_study_data(self, verb: str, conjugation_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        norm = normalize_verb(verb)
        study = self._fallback.get_study_data(verb, conjugation_data)

        # If conjugation_data has scraped_examples, inject them
        if conjugation_data and conjugation_data.get("scraped_examples"):
            study["examples"] = [
                {"tense": f"Exemple #{i}", "fr": fr, "en": en}
                for i, (fr, en) in enumerate(conjugation_data["scraped_examples"], 1)
            ]
            study["examples_source"] = "frenchdictionary.com"
        else:
            # Check if live scrape works
            success, scraped_examples, status = self._scraper.fetch_word_examples(norm)
            if success and scraped_examples:
                study["examples"] = [
                    {"tense": f"Exemple #{i}", "fr": fr, "en": en}
                    for i, (fr, en) in enumerate(scraped_examples, 1)
                ]
                study["examples_source"] = "frenchdictionary.com"
            else:
                study["cf_blocked"] = True
                study["cf_url"] = f"{self._base_url}/examples/{urllib.parse.quote(norm)}?lang=fr"
                study["cf_status"] = status

        return study
