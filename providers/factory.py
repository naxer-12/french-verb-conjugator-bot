"""
Provider Factory for French Conjugation Engines.
Provides dynamic provider selection based on environment configuration or runtime parameters.
"""

import os
from typing import Dict, Optional

from .base import BaseConjugationProvider
from .lingolia_provider import LingoliaProvider
from .french_dictionary_provider import FrenchDictionaryProvider
from .hybrid_provider import HybridProvider

_ACTIVE_PROVIDER: Optional[BaseConjugationProvider] = None


def get_provider(name: Optional[str] = None) -> BaseConjugationProvider:
    """
    Returns an instance of the requested or configured conjugation provider.
    Priority:
    1. Explicit 'name' argument
    2. CONJUGATION_PROVIDER environment variable
    3. Default: 'hybrid' (Lingolia + Pedagogical Study Engine)
    """
    global _ACTIVE_PROVIDER
    if name is None:
        if _ACTIVE_PROVIDER is not None:
            return _ACTIVE_PROVIDER
        name = os.getenv("CONJUGATION_PROVIDER", "hybrid").strip().lower()

    key = name.lower()
    if key in ("hybrid", "default"):
        provider = HybridProvider()
    elif key in ("lingolia", "lingolia_only"):
        provider = LingoliaProvider()
    elif key in ("frenchdictionary", "french_dict"):
        provider = FrenchDictionaryProvider()
    else:
        # Fallback to hybrid
        provider = HybridProvider()

    if _ACTIVE_PROVIDER is None and name == os.getenv("CONJUGATION_PROVIDER", "hybrid").strip().lower():
        _ACTIVE_PROVIDER = provider

    return provider


def set_provider(provider: BaseConjugationProvider) -> None:
    """Explicitly sets the active provider instance (useful for testing and dependency injection)."""
    global _ACTIVE_PROVIDER
    _ACTIVE_PROVIDER = provider
