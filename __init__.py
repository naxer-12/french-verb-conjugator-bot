"""
French Verb Conjugator Bot package.
Powered by python-telegram-bot and Lingolia French Scraper Engine.
"""

from .lingolia import (
    LingoliaScraper,
    normalize_verb,
    get_conjugation,
    autocomplete,
)
from .bot import (
    format_conjugation_message,
    format_all_moods,
    build_conjugation_keyboard,
    build_suggestions_keyboard,
    format_not_found_message,
    build_application,
)
from .pedagogy import (
    MOOD_GUIDES,
    TENSE_GUIDES,
    get_verb_study_data,
    format_student_study_card,
    format_examples_and_synonyms,
)
from .providers import (
    BaseConjugationProvider,
    LingoliaProvider,
    FrenchDictionaryProvider,
    HybridProvider,
    get_provider,
    set_provider,
)

__all__ = [
    "LingoliaScraper",
    "normalize_verb",
    "get_conjugation",
    "autocomplete",
    "format_conjugation_message",
    "format_all_moods",
    "build_conjugation_keyboard",
    "build_suggestions_keyboard",
    "format_not_found_message",
    "build_application",
    "MOOD_GUIDES",
    "TENSE_GUIDES",
    "get_verb_study_data",
    "format_student_study_card",
    "format_examples_and_synonyms",
    "BaseConjugationProvider",
    "LingoliaProvider",
    "FrenchDictionaryProvider",
    "HybridProvider",
    "get_provider",
    "set_provider",
]
