"""
Unit tests for the dedicated FrenchDictionary scraper.
"""

import unittest
from unittest.mock import patch, MagicMock
import urllib.error

try:
    from french_verb_conjugator_bot.frenchdictionary_scraper import (
        FrenchDictionaryScraper,
        FrenchDictionaryHTMLParser,
    )
except ImportError:
    from frenchdictionary_scraper import (
        FrenchDictionaryScraper,
        FrenchDictionaryHTMLParser,
    )


class TestFrenchDictionaryScraper(unittest.TestCase):
    """Test suite for direct FrenchDictionary.com scraping."""

    def test_html_parser_extracts_examples(self):
        """Test parser with simulated FrenchDictionary HTML markup."""
        sample_html = """
        <div class="dictionary-entry">
            <div class="example-pair">
                <span lang="fr" class="source">Je dois travailler dur pour réussir.</span>
                <span lang="en" class="target">I have to work hard to succeed.</span>
            </div>
            <div class="example-pair">
                <span lang="fr" class="source">Il travaille dans un bureau à Paris.</span>
                <span lang="en" class="target">He works in an office in Paris.</span>
            </div>
        </div>
        """
        parser = FrenchDictionaryHTMLParser()
        parser.feed(sample_html)
        self.assertGreaterEqual(len(parser.examples), 2)
        self.assertEqual(parser.examples[0][0], "Je dois travailler dur pour réussir.")
        self.assertEqual(parser.examples[0][1], "I have to work hard to succeed.")

    def test_cloudflare_403_handling(self):
        """Test that Cloudflare HTTP 403 challenge is caught cleanly."""
        scraper = FrenchDictionaryScraper()

        mock_err = urllib.error.HTTPError(
            url="https://www.frenchdictionary.com/examples/travailler?lang=fr",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=None,
        )

        with patch.object(scraper.opener, "open", side_effect=mock_err):
            success, examples, status = scraper.fetch_word_examples("travailler")
            self.assertFalse(success)
            self.assertEqual(examples, [])
            self.assertIn("403 Forbidden", status)
            self.assertIn("Cloudflare Turnstile", status)

    def test_live_attempt_reports_cloudflare_challenge(self):
        """
        Live probe to verify what frenchdictionary.com actually returns.
        Documents the real-world Cloudflare block.
        """
        scraper = FrenchDictionaryScraper()
        success, examples, status = scraper.fetch_word_examples("travailler")
        # On standard environments, this will report HTTP 403 Cloudflare challenge
        if not success:
            self.assertIn("403", status)


if __name__ == "__main__":
    unittest.main()
