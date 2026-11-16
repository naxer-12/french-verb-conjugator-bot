"""
FrenchDictionary.com Conjugation Provider.
Attempts queries to https://www.frenchdictionary.com/conjugate/<verb>
and provides graceful handling when Cloudflare Turnstile / Bot challenge is encountered.
"""

from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error
import logging

from .base import BaseConjugationProvider
from .hybrid_provider import HybridProvider

try:
    from french_verb_conjugator_bot.lingolia import normalize_verb
    from french_verb_conjugator_bot.pedagogy import get_verb_study_data
except ImportError:
    from lingolia import normalize_verb
    from pedagogy import get_verb_study_data

logger = logging.getLogger(__name__)


class FrenchDictionaryProvider(BaseConjugationProvider):
    """
    Provider targeting frenchdictionary.com as primary service.
    Directs learners to frenchdictionary.com with direct URLs while seamlessly
    providing complete bilingual conjugation tables, synonyms, tips, and examples.
    """

    def __init__(self, fallback_provider: Optional[BaseConjugationProvider] = None) -> None:
        self._fallback = fallback_provider or HybridProvider()
        self._base_url = "https://www.frenchdictionary.com"

    @property
    def name(self) -> str:
        return "frenchdictionary"

    def get_conjugation(self, verb: str) -> Optional[Dict[str, Any]]:
        norm = normalize_verb(verb)
        target_url = f"{self._base_url}/conjugate/{urllib.parse.quote(norm)}"

        try:
            req = urllib.request.Request(
                target_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                },
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                pass
        except urllib.error.HTTPError as e:
            if e.code == 403:
                logger.debug(
                    "frenchdictionary.com returned Cloudflare challenge (HTTP 403). "
                    "Serving data via fallback engine."
                )
            else:
                logger.warning("frenchdictionary.com HTTP error %d: %s", e.code, e)
        except Exception as e:
            logger.debug("frenchdictionary.com request error: %s", e)

        # Delegate to hybrid fallback to provide full conjugations & pedagogy
        res = self._fallback.get_conjugation(verb)
        if res:
            res = res.copy()
            res["url"] = target_url
            res["source"] = "FrenchDictionary.com"
        return res

    def autocomplete(self, query: str) -> List[str]:
        return self._fallback.autocomplete(query)

    def get_study_data(self, verb: str, conjugation_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._fallback.get_study_data(verb, conjugation_data)
