"""
Conjugation and Vocabulary Providers package.
Allows seamlessly selecting and swapping between data providers.
"""

from .base import BaseConjugationProvider
from .lingolia_provider import LingoliaProvider
from .french_dictionary_provider import FrenchDictionaryProvider
from .hybrid_provider import HybridProvider
from .factory import get_provider, set_provider

__all__ = [
    "BaseConjugationProvider",
    "LingoliaProvider",
    "FrenchDictionaryProvider",
    "HybridProvider",
    "get_provider",
    "set_provider",
]
