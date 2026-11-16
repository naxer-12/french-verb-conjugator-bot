"""
Unit tests for the Lingolia French Scraper Engine.
Validates regular verbs, auxiliary verbs, reflexive verbs, invalid verbs,
autocomplete, input normalization, and caching.
"""

import unittest
try:
    from french_verb_conjugator_bot.lingolia import (
        LingoliaScraper,
        normalize_verb,
        get_conjugation,
        autocomplete,
    )
except ImportError:
    from lingolia import (
        LingoliaScraper,
        normalize_verb,
        get_conjugation,
        autocomplete,
    )


class TestLingoliaScraper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scraper = LingoliaScraper()

    def test_normalize_verb(self):
        """Test input normalization for case, whitespace, punctuation, and curly apostrophes."""
        self.assertEqual(normalize_verb("  parler  "), "parler")
        self.assertEqual(normalize_verb("PARLER"), "parler")
        self.assertEqual(normalize_verb("s’appeler"), "s'appeler")
        self.assertEqual(normalize_verb("s‘appeler"), "s'appeler")
        self.assertEqual(normalize_verb("  se lever ! "), "se lever")
        self.assertEqual(normalize_verb(""), "")
        self.assertEqual(normalize_verb("...manger..."), "manger")

    def test_regular_verb_parler(self):
        """Test conjugation extraction for a regular -er verb (parler)."""
        data = self.scraper.get_conjugation("parler")
        self.assertIsNotNone(data, "Expected conjugation data for 'parler'")
        
        # Non-conjugated forms
        self.assertEqual(data.get("infinitif"), "parler")
        self.assertEqual(data.get("participe_passe"), "parlé")
        self.assertEqual(data.get("participe_present"), "parlant")
        self.assertEqual(data.get("auxiliaire"), "avoir")
        
        # Verify non_conjugated subdict
        non_conj = data.get("formes_non_conjuguees", {})
        self.assertEqual(non_conj.get("infinitif"), "parler")
        self.assertEqual(non_conj.get("auxiliaire"), "avoir")

        # Verify Moods exist
        moods = data.get("moods", {})
        for mood in ["Indicatif", "Conditionnel", "Subjonctif", "Impératif"]:
            self.assertIn(mood, moods, f"Mood '{mood}' missing from moods dict")
            self.assertIn(mood, data, f"Mood '{mood}' missing as top-level key")

        # Check Indicatif Présent rows
        ind_pres = moods["Indicatif"].get("Présent", [])
        self.assertGreaterEqual(len(ind_pres), 6)
        subjects = [row[0] for row in ind_pres]
        verbs = [row[1] for row in ind_pres]
        self.assertIn("je", subjects)
        self.assertIn("parle", verbs)
        self.assertIn("parlent", verbs)

        # Check Impératif rows
        imp_pres = moods["Impératif"].get("Présent", [])
        self.assertEqual(len(imp_pres), 3)

    def test_auxiliary_verb_etre(self):
        """Test conjugation extraction for the irregular auxiliary verb 'être'."""
        data = self.scraper.get_conjugation("être")
        self.assertIsNotNone(data, "Expected conjugation data for 'être'")
        
        self.assertEqual(data.get("infinitif"), "être")
        self.assertEqual(data.get("participe_passe"), "été")
        self.assertEqual(data.get("participe_present"), "étant")
        self.assertEqual(data.get("auxiliaire"), "avoir")

        ind_pres = data.get("moods", {}).get("Indicatif", {}).get("Présent", [])
        pairs = dict(ind_pres)
        self.assertEqual(pairs.get("je"), "suis")
        self.assertEqual(pairs.get("tu"), "es")
        self.assertEqual(pairs.get("il"), "est")

    def test_irregular_verbs_avoir_aller_faire(self):
        """Test irregular French verbs (avoir, aller, faire)."""
        # avoir
        d_avoir = get_conjugation("avoir")
        self.assertIsNotNone(d_avoir)
        self.assertEqual(d_avoir.get("auxiliaire"), "avoir")
        self.assertEqual(d_avoir.get("participe_passe"), "eu")

        # aller (takes être)
        d_aller = get_conjugation("aller")
        self.assertIsNotNone(d_aller)
        self.assertEqual(d_aller.get("auxiliaire"), "être")
        self.assertEqual(d_aller.get("participe_passe"), "allé")

        # faire
        d_faire = get_conjugation("faire")
        self.assertIsNotNone(d_faire)
        self.assertEqual(d_faire.get("auxiliaire"), "avoir")
        self.assertEqual(d_faire.get("participe_passe"), "fait")

    def test_reflexive_verb_se_lever(self):
        """Test conjugation extraction for reflexive verb 'se lever'."""
        data = self.scraper.get_conjugation("se lever")
        self.assertIsNotNone(data, "Expected conjugation data for 'se lever'")
        
        self.assertEqual(data.get("infinitif"), "se lever")
        self.assertEqual(data.get("auxiliaire"), "être")
        
        ind_pres = data.get("moods", {}).get("Indicatif", {}).get("Présent", [])
        pairs = dict(ind_pres)
        self.assertEqual(pairs.get("je"), "me lève")
        self.assertEqual(pairs.get("tu"), "te lèves")

    def test_reflexive_verb_curly_apostrophe(self):
        """Test reflexive verb with curly apostrophe 's’appeler'."""
        data = self.scraper.get_conjugation("s’appeler")
        self.assertIsNotNone(data, "Expected conjugation data for 's’appeler'")
        
        self.assertEqual(data.get("auxiliaire"), "être")
        ind_pres = data.get("moods", {}).get("Indicatif", {}).get("Présent", [])
        pairs = dict(ind_pres)
        # Handle either curly or straight apostrophe in output
        je_form = pairs.get("je", "")
        self.assertTrue(
            je_form in ("m’appelle", "m'appelle"),
            f"Unexpected form for 'je' in s'appeler: {je_form}"
        )

    def test_invalid_verb_detection(self):
        """Test that invalid gibberish verb returns None."""
        data = self.scraper.get_conjugation("azertyuiop")
        self.assertIsNone(data, "Expected None for invalid verb 'azertyuiop'")
        
        # Test empty input
        self.assertIsNone(self.scraper.get_conjugation(""))

    def test_autocomplete(self):
        """Test autocomplete endpoint with prefix 'parl'."""
        suggestions = self.scraper.autocomplete("parl")
        self.assertIsInstance(suggestions, list)
        self.assertIn("parler", suggestions)

        # Test empty or gibberish prefix
        empty_res = self.scraper.autocomplete("xyznonexistentverb123")
        self.assertEqual(empty_res, [])

    def test_caching(self):
        """Test that LRU cache is working on get_conjugation and autocomplete."""
        # Query twice to trigger cache hit
        self.scraper.get_conjugation("parler")
        self.scraper.get_conjugation("parler")
        cache_info_conj = self.scraper.get_conjugation.cache_info()
        self.assertGreater(cache_info_conj.hits, 0)

        self.scraper.autocomplete("parl")
        self.scraper.autocomplete("parl")
        cache_info_auto = self.scraper.autocomplete.cache_info()
        self.assertGreater(cache_info_auto.hits, 0)


if __name__ == "__main__":
    unittest.main()
