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
]
