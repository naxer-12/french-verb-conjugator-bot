"""
Unit tests for the French Verb Conjugator Telegram Bot logic.

Validates:
- Message formatting & monospaced column alignment
- HTML escaping of unsafe input
- Inline keyboard active state markers and callback data
- Message chunking algorithm for length > 3800 characters
- Token retrieval and environment validation
- Not found messages & fallback suggestions
- Handler and application configuration
"""

import os
import unittest
from unittest.mock import patch, MagicMock

try:
    from french_verb_conjugator_bot.bot import (
        format_conjugation_message,
        format_all_moods,
        build_conjugation_keyboard,
        build_suggestions_keyboard,
        format_not_found_message,
        get_bot_token,
        build_application,
        SUPPORTED_MOODS,
    )
    from french_verb_conjugator_bot.lingolia import normalize_verb, get_conjugation
    from french_verb_conjugator_bot.pedagogy import (
        get_verb_study_data,
        format_student_study_card,
        format_examples_and_synonyms,
        infer_verb_group,
    )
except ImportError:
    from bot import (
        format_conjugation_message,
        format_all_moods,
        build_conjugation_keyboard,
        build_suggestions_keyboard,
        format_not_found_message,
        get_bot_token,
        build_application,
        SUPPORTED_MOODS,
    )
    from lingolia import normalize_verb, get_conjugation
    from pedagogy import (
        get_verb_study_data,
        format_student_study_card,
        format_examples_and_synonyms,
        infer_verb_group,
    )


class TestBotLogic(unittest.TestCase):
    def setUp(self):
        # Sample mock verb data
        self.sample_verb_data = {
            "verb": "parler",
            "infinitif": "parler",
            "participe_present": "parlant",
            "participe_passe": "parlé",
            "auxiliaire": "avoir",
            "formes_non_conjuguees": {
                "infinitif": "parler",
                "participe_present": "parlant",
                "participe_passe": "parlé",
                "auxiliaire": "avoir",
            },
            "moods": {
                "Indicatif": {
                    "Présent": [
                        ("je", "parle"),
                        ("tu", "parles"),
                        ("il/elle/on", "parle"),
                        ("nous", "parlons"),
                        ("vous", "parlez"),
                        ("ils/elles", "parlent"),
                    ],
                    "Imparfait": [
                        ("je", "parlais"),
                        ("tu", "parlais"),
                        ("il", "parlait"),
                        ("nous", "parlions"),
                        ("vous", "parliez"),
                        ("ils", "parlaient"),
                    ],
                },
                "Conditionnel": {
                    "Présent": [
                        ("je", "parlerais"),
                        ("tu", "parlerais"),
                        ("il", "parlerait"),
                        ("nous", "parlerions"),
                        ("vous", "parleriez"),
                        ("ils", "parleraient"),
                    ]
                },
                "Subjonctif": {
                    "Présent": [
                        ("que je", "parle"),
                        ("que tu", "parles"),
                        ("qu'il", "parle"),
                        ("que nous", "parlions"),
                        ("que vous", "parliez"),
                        ("qu'ils", "parlent"),
                    ]
                },
                "Impératif": {
                    "Présent": [
                        ("(tu)", "parle!"),
                        ("(nous)", "parlons!"),
                        ("(vous)", "parlez!"),
                    ]
                },
            },
            "url": "https://francais.lingolia.com/en/grammar/conjugator?verb=parler",
        }

    # -----------------------------------------------------------------------
    # Environment & Token Validation Tests
    # -----------------------------------------------------------------------

    def test_token_loading_valid(self):
        """Test that get_bot_token retrieves token from env."""
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"}):
            token = get_bot_token()
            self.assertEqual(token, "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")

    def test_token_loading_missing_raises_value_error(self):
        """Test that missing or placeholder token raises ValueError."""
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}, clear=True):
            with self.assertRaises(ValueError):
                get_bot_token()

        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "your_telegram_bot_token_here"}):
            with self.assertRaises(ValueError):
                get_bot_token()

    # -----------------------------------------------------------------------
    # Message Formatting & Monospaced Alignment Tests
    # -----------------------------------------------------------------------

    def test_format_conjugation_message_structure(self):
        """Test message header, non-conjugated forms, mood block, and divider."""
        msg = format_conjugation_message(self.sample_verb_data, mood="Indicatif")
        
        # Verify header & dividers
        self.assertIn("📖 <b>CONJUGAISON : PARLER</b>", msg)
        self.assertIn("━━━━━━━━━━━━━━━━━━━━", msg)
        
        # Verify non-conjugated section
        self.assertIn("📌 <b>Formes non conjuguées</b>", msg)
        self.assertIn("• <b>Infinitif :</b> parler", msg)
        self.assertIn("• <b>Participe présent :</b> parlant", msg)
        self.assertIn("• <b>Participe passé :</b> parlé", msg)
        self.assertIn("• <b>Auxiliaire :</b> avoir", msg)

        # Verify mood section
        self.assertIn("🔹 <b>MODE INDICATIF</b>", msg)
        self.assertIn("🕒 <b>Présent</b>", msg)
        self.assertIn("🕒 <b>Imparfait</b>", msg)

    def test_format_conjugation_message_column_alignment(self):
        """Test that subjects and verb stems are cleanly aligned inside <code>...</code> tags."""
        msg = format_conjugation_message(self.sample_verb_data, mood="Indicatif")
        
        # Extract lines for Présent
        code_lines = [line for line in msg.split("\n") if line.startswith("<code>") and line.endswith("</code>")]
        self.assertGreaterEqual(len(code_lines), 6)

        # In Présent, 'il/elle/on' has 10 chars. Padding should align verb stems!
        # Max subject len is 10. Each line should be:
        # <code>{subject.ljust(10)}  {verb}</code>
        for code_line in code_lines[:6]:
            content = code_line[6:-7]  # strip <code> and </code>
            # There should be at least two spaces between subject column and verb column
            self.assertIn("  ", content)
            # Find the verb start position (after the subject padding + 2 spaces)
            # Since max subject len is 10, verb start should be at column index 12
            parts = content.split("  ")
            subject_part = parts[0]
            verb_part = "  ".join(parts[1:]).strip()
            self.assertEqual(len(content) - len(verb_part), 12)

    def test_format_conjugation_message_html_escaping(self):
        """Test that special characters (<, >, &) in verb forms or subjects are escaped."""
        evil_data = {
            "verb": "<evil&verb>",
            "infinitif": "<evil&verb>",
            "participe_present": "<pres>",
            "participe_passe": "<passe>",
            "auxiliaire": "<aux>",
            "moods": {
                "Indicatif": {
                    "<Tense&1>": [
                        ("<sub>", "<form>"),
                    ]
                }
            }
        }
        msg = format_conjugation_message(evil_data, mood="Indicatif")
        self.assertNotIn("<evil&verb>", msg)
        self.assertIn("&lt;EVIL&amp;VERB&gt;", msg)
        self.assertIn("&lt;pres&gt;", msg)
        self.assertIn("&lt;passe&gt;", msg)
        self.assertIn("&lt;aux&gt;", msg)
        self.assertIn("&lt;Tense&amp;1&gt;", msg)
        self.assertIn("&lt;sub&gt;", msg)
        self.assertIn("&lt;form&gt;", msg)

    def test_format_conjugation_message_empty_or_unknown_mood(self):
        """Test graceful formatting when requested mood is not present."""
        msg = format_conjugation_message(self.sample_verb_data, mood="Inconnu")
        self.assertIn("<i>Aucune conjugaison disponible pour le mode Inconnu.</i>", msg)

        # Empty data handling
        self.assertEqual(format_conjugation_message({}), "")

    # -----------------------------------------------------------------------
    # Inline Keyboard Generation Tests
    # -----------------------------------------------------------------------

    def test_build_conjugation_keyboard_active_state(self):
        """Test that active mood button receives '✅' badge while inactive receive '🔸'."""
        kb_ind = build_conjugation_keyboard("parler", active_mood="Indicatif")
        buttons_ind = {b.callback_data: b.text for row in kb_ind.inline_keyboard for b in row if b.callback_data}

        self.assertEqual(buttons_ind["tab:parler:Indicatif"], "✅ Indicatif")
        self.assertEqual(buttons_ind["tab:parler:Conditionnel"], "🔸 Conditionnel")
        self.assertEqual(buttons_ind["tab:parler:Subjonctif"], "🔸 Subjonctif")
        self.assertEqual(buttons_ind["tab:parler:Impératif"], "🔸 Impératif")
        self.assertEqual(buttons_ind["all:parler"], "📚 Tout afficher")

        # Test switching active mood to Subjonctif
        kb_subj = build_conjugation_keyboard("parler", active_mood="Subjonctif")
        buttons_subj = {b.callback_data: b.text for row in kb_subj.inline_keyboard for b in row if b.callback_data}

        self.assertEqual(buttons_subj["tab:parler:Indicatif"], "🔸 Indicatif")
        self.assertEqual(buttons_subj["tab:parler:Conditionnel"], "🔸 Conditionnel")
        self.assertEqual(buttons_subj["tab:parler:Subjonctif"], "✅ Subjonctif")
        self.assertEqual(buttons_subj["tab:parler:Impératif"], "🔸 Impératif")

    def test_build_conjugation_keyboard_url_button(self):
        """Test URL button creation for Lingolia."""
        kb = build_conjugation_keyboard("parler", url="https://example.com/parler")
        url_buttons = [b for row in kb.inline_keyboard for b in row if b.url]
        self.assertEqual(len(url_buttons), 1)
        self.assertEqual(url_buttons[0].text, "🌐 Lingolia")
        self.assertEqual(url_buttons[0].url, "https://example.com/parler")

    def test_build_conjugation_keyboard_frenchdictionary_url_button(self):
        """Test URL button creation for FrenchDictionary."""
        kb = build_conjugation_keyboard("parler", url="https://www.frenchdictionary.com/conjugate/parler")
        url_buttons = [b for row in kb.inline_keyboard for b in row if b.url]
        self.assertEqual(len(url_buttons), 1)
        self.assertEqual(url_buttons[0].text, "🌐 FrenchDictionary")
        self.assertEqual(url_buttons[0].url, "https://www.frenchdictionary.com/conjugate/parler")

    def test_build_suggestions_keyboard(self):
        """Test candidate suggestion keyboard buttons."""
        suggestions = ["parler", "partir", "parvenir", "parcourir"]
        kb = build_suggestions_keyboard(suggestions)
        btn_data = [b.callback_data for row in kb.inline_keyboard for b in row]
        self.assertEqual(btn_data, ["conj:parler", "conj:partir", "conj:parvenir", "conj:parcourir"])

    # -----------------------------------------------------------------------
    # Chunking Algorithm Tests ("Tout afficher")
    # -----------------------------------------------------------------------

    def test_format_all_moods_under_3800_chars(self):
        """Test that small verb under 3800 chars returns a single chunk."""
        small_verb_data = {
            "verb": "aller",
            "infinitif": "aller",
            "participe_present": "allant",
            "participe_passe": "allé",
            "auxiliaire": "être",
            "moods": {
                "Impératif": {
                    "Présent": [("(tu)", "va!"), ("(nous)", "allons!"), ("(vous)", "allez!")]
                }
            }
        }
        chunks = format_all_moods(small_verb_data)
        self.assertEqual(len(chunks), 1)
        self.assertLessEqual(len(chunks[0]), 3800)
        self.assertIn("🔹 <b>MODE IMPÉRATIF</b>", chunks[0])

    def test_format_all_moods_over_3800_chars_chunks_cleanly(self):
        """Test that verbs whose full conjugation exceeds 3800 characters are partitioned without breaking HTML tags."""
        # Using real full conjugation of 'parler' from Lingolia scraper
        parler_data = get_conjugation("parler")
        self.assertIsNotNone(parler_data)

        chunks = format_all_moods(parler_data)
        
        # Parler has 15 tenses across 4 moods and exceeds 3800 chars
        self.assertGreaterEqual(len(chunks), 2)
        
        for i, chunk in enumerate(chunks, 1):
            # Must strictly adhere to Telegram's 4,096 char limit (and our 3,800 threshold)
            self.assertLessEqual(len(chunk), 3800, f"Chunk {i} exceeded 3800 limit ({len(chunk)} chars)")
            
            # Check balanced HTML tags
            self.assertEqual(chunk.count("<b>"), chunk.count("</b>"), f"Unbalanced <b> tags in chunk {i}")
            self.assertEqual(chunk.count("<code>"), chunk.count("</code>"), f"Unbalanced <code> tags in chunk {i}")
            self.assertEqual(chunk.count("<i>"), chunk.count("</i>"), f"Unbalanced <i> tags in chunk {i}")

        # Part 1 should contain Part 1/2 indicator and Indicatif
        self.assertIn("(Partie 1/2)", chunks[0])
        self.assertIn("🔹 <b>MODE INDICATIF</b>", chunks[0])

        # Part 2 should contain Part 2/2 indicator and remaining moods
        self.assertIn("(Partie 2/2)", chunks[1])
        self.assertIn("🔹 <b>MODE CONDITIONNEL</b>", chunks[1])
        self.assertIn("🔹 <b>MODE SUBJONCTIF</b>", chunks[1])
        self.assertIn("🔹 <b>MODE IMPÉRATIF</b>", chunks[1])

    # -----------------------------------------------------------------------
    # Error & Fallback Suggestions Logic
    # -----------------------------------------------------------------------

    def test_format_not_found_message(self):
        """Test not found messages with and without suggestions."""
        msg_with_sugg = format_not_found_message("parle", has_suggestions=True)
        self.assertIn("Vouliez-vous dire :", msg_with_sugg)
        self.assertIn("parle", msg_with_sugg)

        msg_no_sugg = format_not_found_message("xyzunknown", has_suggestions=False)
        self.assertIn("Lingolia attend la forme <b>infinitif</b>", msg_no_sugg)
        self.assertIn("Vérifiez l'orthographe", msg_no_sugg)

    def test_normalization_in_bot(self):
        """Test normalization handles spaces, cases, and curly quotes."""
        self.assertEqual(normalize_verb("  PARLER  "), "parler")
        self.assertEqual(normalize_verb("s’asseoir"), "s'asseoir")
        self.assertEqual(normalize_verb("! manger !"), "manger")

    # -----------------------------------------------------------------------
    # Application & Handlers Configuration
    # -----------------------------------------------------------------------

    def test_build_application_handlers(self):
        """Test that build_application registers all required command and message handlers."""
        app = build_application(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        handler_types = [type(h).__name__ for group in app.handlers.values() for h in group]

        self.assertIn("CommandHandler", handler_types)
        self.assertIn("MessageHandler", handler_types)
        self.assertIn("CallbackQueryHandler", handler_types)
        self.assertIn("InlineQueryHandler", handler_types)


    # -----------------------------------------------------------------------
    # Bilingual Pedagogical & Student Learning Tests
    # -----------------------------------------------------------------------

    def test_pedagogy_curated_verb(self):
        """Test curated verb study data retrieval (parler)."""
        data = get_verb_study_data("parler")
        self.assertEqual(data["verb"], "parler")
        self.assertEqual(data["meaning_en"], "To speak, to talk")
        self.assertIn("1er groupe", data["group"])
        self.assertGreaterEqual(len(data["synonyms"]), 3)
        self.assertGreaterEqual(len(data["examples"]), 2)

    def test_pedagogy_dynamic_inference(self):
        """Test morphological inference for arbitrary verbs."""
        er_data = infer_verb_group("danser")
        self.assertIn("1er groupe", er_data["group_fr"])
        self.assertEqual(er_data["auxiliaire"], "avoir")

        refl_data = infer_verb_group("se coucher")
        self.assertTrue(refl_data["is_reflexive"])
        self.assertEqual(refl_data["auxiliaire"], "être")

    def test_format_student_study_card(self):
        """Test student study guide formatting with tips and bilingual guides."""
        card = format_student_study_card("parler", self.sample_verb_data)
        self.assertIn("FICHE ÉTUDIANT : PARLER", card)
        self.assertIn("To speak, to talk", card)
        self.assertIn("Conseil Pédagogique / Student Study Tip", card)
        self.assertIn("Guide Pratique des 4 Modes", card)

    def test_format_examples_and_synonyms(self):
        """Test synonyms list and bilingual contextual example sentences."""
        ex_card = format_examples_and_synonyms("parler", self.sample_verb_data)
        self.assertIn("EXEMPLES & SYNONYMES : PARLER", ex_card)
        self.assertIn("Synonymes utiles / Related Verbs", ex_card)
        self.assertIn("discuter", ex_card)
        self.assertIn("Phrases d'exemples bilingues", ex_card)
        self.assertIn("🇫🇷", ex_card)
        self.assertIn("🇬🇧", ex_card)

    def test_keyboard_pedagogy_tabs(self):
        """Test that Exemples and Student tabs appear on the keyboard."""
        kb = build_conjugation_keyboard("parler", active_mood="examples")
        callbacks = {b.callback_data: b.text for row in kb.inline_keyboard for b in row if b.callback_data}
        self.assertIn("tab:parler:examples", callbacks)
        self.assertIn("tab:parler:student", callbacks)
        self.assertIn("✅", callbacks["tab:parler:examples"])
        self.assertIn("🔸", callbacks["tab:parler:student"])


if __name__ == "__main__":
    unittest.main()
