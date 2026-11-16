"""
Lingolia Conjugation Provider.
Fetches accurate conjugation tables from Lingolia Français with session CSRF handling.
"""

from typing import Any, Dict, List, Optional
from .base import BaseConjugationProvider

try:
    from french_verb_conjugator_bot.lingolia import LingoliaScraper, normalize_verb
    from french_verb_conjugator_bot.pedagogy import get_verb_study_data
except ImportError:
    from lingolia import LingoliaScraper, normalize_verb
    from pedagogy import get_verb_study_data


class LingoliaProvider(BaseConjugationProvider):
    """
    Provider backed by Lingolia Français for conjugation tables,
    paired with internal pedagogical dictionaries for student guides.
    """

    def __init__(self, scraper: Optional[LingoliaScraper] = None) -> None:
        self._scraper = scraper or LingoliaScraper()

    @property
    def name(self) -> str:
        return "lingolia"

    def get_conjugation(self, verb: str) -> Optional[Dict[str, Any]]:
        return self._scraper.get_conjugation(verb)

    def autocomplete(self, query: str) -> List[str]:
        return self._scraper.autocomplete(query)

    def get_study_data(self, verb: str, conjugation_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return get_verb_study_data(verb, conjugation_data)
