"""
Unit tests for the Pluggable Provider Architecture.
Validates:
- BaseConjugationProvider interface contract
- LingoliaProvider delegation
- FrenchDictionaryProvider graceful Cloudflare challenge handling & fallback
- HybridProvider student data enrichment
- Factory provider resolution via CONJUGATION_PROVIDER env var
"""

import os
import unittest
from unittest.mock import patch, MagicMock

try:
    from french_verb_conjugator_bot.providers import (
        BaseConjugationProvider,
        LingoliaProvider,
        FrenchDictionaryProvider,
        HybridProvider,
        get_provider,
        set_provider,
    )
except ImportError:
    from providers import (
        BaseConjugationProvider,
        LingoliaProvider,
        FrenchDictionaryProvider,
        HybridProvider,
        get_provider,
        set_provider,
    )


class TestProviders(unittest.TestCase):
    """Test suite for the pluggable conjugation providers."""

    def test_factory_default_is_hybrid(self):
        """Test that default provider is HybridProvider."""
        with patch.dict(os.environ, {}, clear=True):
            set_provider(None)
            p = get_provider()
            self.assertIsInstance(p, HybridProvider)
            self.assertEqual(p.name, "hybrid")

    def test_factory_env_selection(self):
        """Test selecting provider via CONJUGATION_PROVIDER env var."""
        with patch.dict(os.environ, {"CONJUGATION_PROVIDER": "lingolia"}):
            set_provider(None)
            p = get_provider()
            self.assertIsInstance(p, LingoliaProvider)
            self.assertEqual(p.name, "lingolia")

        with patch.dict(os.environ, {"CONJUGATION_PROVIDER": "frenchdictionary"}):
            set_provider(None)
            p = get_provider()
            self.assertIsInstance(p, FrenchDictionaryProvider)
            self.assertEqual(p.name, "frenchdictionary")

    def test_lingolia_provider_methods(self):
        """Test LingoliaProvider delegating to scraper."""
        mock_scraper = MagicMock()
        mock_scraper.get_conjugation.return_value = {"verb": "parler"}
        mock_scraper.autocomplete.return_value = ["parler", "partir"]

        provider = LingoliaProvider(scraper=mock_scraper)
        res = provider.get_conjugation("parler")
        self.assertEqual(res, {"verb": "parler"})
        self.assertEqual(provider.autocomplete("parl"), ["parler", "partir"])

        study = provider.get_study_data("parler")
        self.assertEqual(study["meaning_en"], "To speak, to talk")

    def test_french_dictionary_provider_fallback_on_cloudflare(self):
        """
        Test that FrenchDictionaryProvider catches Cloudflare 403 challenge
        and seamlessly uses its fallback provider without raising an exception.
        """
        mock_fallback = MagicMock()
        mock_fallback.get_conjugation.return_value = {"verb": "être"}
        mock_fallback.autocomplete.return_value = ["être"]

        provider = FrenchDictionaryProvider(fallback_provider=mock_fallback)
        self.assertEqual(provider.name, "frenchdictionary")

        # Calling get_conjugation should attempt request and fallback cleanly
        res = provider.get_conjugation("être")
        self.assertEqual(res, {"verb": "être"})
        mock_fallback.get_conjugation.assert_called_with("être")

    def test_hybrid_provider_enrichment(self):
        """Test HybridProvider provides both conjugations and enriched study data."""
        mock_lingolia = MagicMock()
        mock_lingolia.get_conjugation.return_value = {
            "verb": "parler",
            "infinitif": "parler",
            "auxiliaire": "avoir",
        }
        mock_lingolia.autocomplete.return_value = ["parler"]

        provider = HybridProvider(lingolia_provider=mock_lingolia)
        self.assertEqual(provider.name, "hybrid")

        conj = provider.get_conjugation("parler")
        self.assertEqual(conj["verb"], "parler")

        study = provider.get_study_data("parler", conj)
        self.assertEqual(study["meaning_en"], "To speak, to talk")
        self.assertGreaterEqual(len(study["synonyms"]), 3)
        self.assertGreaterEqual(len(study["examples"]), 2)


if __name__ == "__main__":
    unittest.main()
