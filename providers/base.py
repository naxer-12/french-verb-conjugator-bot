"""
Abstract Base Provider for French Verb Conjugation and Pedagogical Data.
Defines the standard interface that all conjugation and vocabulary providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseConjugationProvider(ABC):
    """
    Abstract interface for French conjugation and pedagogical data providers.
    Allows seamlessly swapping data sources (Lingolia, FrenchDictionary, Wiktionary, etc.).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the human-readable identifier of the provider."""
        pass

    @abstractmethod
    def get_conjugation(self, verb: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves full conjugation data for the specified French verb.
        Returns a dictionary containing:
        - 'verb': canonical infinitive
        - 'infinitif', 'participe_present', 'participe_passe', 'auxiliaire'
        - 'moods': Dict[Mood, Dict[Tense, List[Tuple[subject, verb_form]]]]
        - 'url': optional source reference URL
        Returns None if verb cannot be conjugated.
        """
        pass

    @abstractmethod
    def autocomplete(self, query: str) -> List[str]:
        """
        Returns a list of suggested infinitive French verbs for live typing or fallback suggestions.
        """
        pass

    @abstractmethod
    def get_study_data(self, verb: str, conjugation_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Returns rich bilingual pedagogical study data:
        - 'meaning_en', 'meaning_fr'
        - 'group', 'level', 'auxiliaire'
        - 'tip_en', 'tip_fr'
        - 'synonyms': List[Tuple[fr, en]]
        - 'examples': List[Dict[tense, fr, en]]
        """
        pass
