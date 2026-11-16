"""
Pure standard library scraper engine for Lingolia Français Conjugator.

Provides:
- Input normalization (curly quotes, whitespace, punctuation, lowercasing)
- Session token retrieval and persistent cookie handling
- Conjugation scraping and HTML parsing for all 4 French moods and tenses
- Non-conjugated forms extraction (infinitif, participe présent/passé, auxiliaire)
- Live autocomplete API integration with fallback for reflexive prefixes
- In-memory LRU caching for high performance (<1ms cached response)
"""

import functools
import http.cookiejar
from html.parser import HTMLParser
import json
import re
import ssl
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
CONJUGATOR_URL = "https://francais.lingolia.com/en/grammar/conjugator"


def normalize_verb(verb: str) -> str:
    """
    Normalizes a French verb input:
    - Trims leading/trailing whitespace and punctuation (commas, periods, exclamation marks, etc.)
    - Replaces curly apostrophes/quotes (’, ‘, `) with standard straight apostrophe (')
    - Converts to lowercase
    - Collapses multiple whitespace characters
    - Preserves internal apostrophes in reflexive verbs (e.g. s'appeler)
    """
    if not verb:
        return ""
    # Standardize curly quotes and apostrophes
    v = verb.replace("’", "'").replace("‘", "'").replace("`", "'")
    # Strip whitespace and common outer punctuation while keeping letters and accents
    v = v.strip(" \t\n\r.,!?;:\"()[]{}<>«»")
    # Collapse multiple spaces
    v = re.sub(r"\s+", " ", v).lower()
    return v


class LingoliaHTMLParser(HTMLParser):
    """
    HTML parser extracting non-conjugated forms, moods, tenses,
    and (subject, verb_form) pairs from Lingolia's conjugation page.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.non_conjugated: Dict[str, str] = {}
        self.moods: Dict[str, Dict[str, List[Tuple[str, str]]]] = {}

        self.current_mood: Optional[str] = None
        self.current_tense: Optional[str] = None

        # Container visibility tracking
        self._in_inactive_container = False
        self._inactive_depth = 0

        # Element tracking
        self._in_h3 = False
        self._in_th = False
        self._in_td = False
        self._td_class = ""
        self._in_table_verbs = False
        self._in_non_conj_table = False

        self._row_cells: List[Tuple[str, str]] = []
        self._text_buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        attr_dict = {k: v or "" for k, v in attrs}
        classes = attr_dict.get("class", "").split()

        # Track active/inactive containers
        if tag == "div" and "container_tables" in classes:
            if "active" not in classes:
                self._in_inactive_container = True
                self._inactive_depth = 1
            else:
                self._in_inactive_container = False
                self._inactive_depth = 0
        elif self._in_inactive_container and tag == "div":
            self._inactive_depth += 1

        if self._in_inactive_container:
            return

        if tag == "h3":
            self._in_h3 = True
            self._text_buffer = []
        elif tag == "table":
            if "table_verbs" in classes:
                self._in_table_verbs = True
        elif tag == "th":
            self._in_th = True
            self._text_buffer = []
        elif tag == "tr":
            self._row_cells = []
        elif tag == "td":
            self._in_td = True
            self._td_class = attr_dict.get("class", "")
            self._text_buffer = []

    def handle_data(self, data: str):
        if not self._in_inactive_container:
            if self._in_h3 or self._in_th or self._in_td:
                self._text_buffer.append(data)

    def handle_endtag(self, tag: str):
        if self._in_inactive_container and tag == "div":
            self._inactive_depth -= 1
            if self._inactive_depth <= 0:
                self._in_inactive_container = False
            return

        if self._in_inactive_container:
            return

        if tag == "h3" and self._in_h3:
            self._in_h3 = False
            mood_name = re.sub(r"\s+", " ", "".join(self._text_buffer)).strip()
            if mood_name:
                self.current_mood = mood_name
                if self.current_mood not in self.moods:
                    self.moods[self.current_mood] = {}

        elif tag == "th" and self._in_th:
            self._in_th = False
            th_text = re.sub(r"\s+", " ", "".join(self._text_buffer)).strip()
            if "formes non conjuguées" in th_text.lower():
                self._in_non_conj_table = True
            elif self._in_table_verbs and self.current_mood:
                self.current_tense = th_text
                if self.current_tense not in self.moods[self.current_mood]:
                    self.moods[self.current_mood][self.current_tense] = []

        elif tag == "td" and self._in_td:
            self._in_td = False
            raw_text = "".join(self._text_buffer).replace("\xa0", " ")
            clean_text = re.sub(r"\s+", " ", raw_text).strip()
            self._row_cells.append((self._td_class, clean_text))

        elif tag == "tr":
            if self._in_non_conj_table and len(self._row_cells) >= 2:
                key = self._row_cells[0][1].lower()
                val = self._row_cells[1][1]
                if "infinitif" in key:
                    self.non_conjugated["infinitif"] = val
                elif "passé" in key and "participe" in key:
                    self.non_conjugated["participe_passe"] = val
                elif "présent" in key and "participe" in key:
                    self.non_conjugated["participe_present"] = val
                elif "auxiliaire" in key:
                    self.non_conjugated["auxiliaire"] = val
            elif self._in_table_verbs and self.current_mood and self.current_tense:
                subject: Optional[str] = None
                verb_val: Optional[str] = None
                for cls, val in self._row_cells:
                    if "lia_subject" in cls:
                        subject = val
                    elif "lia_verb" in cls:
                        verb_val = val
                if subject is not None and verb_val is not None:
                    self.moods[self.current_mood][self.current_tense].append((subject, verb_val))
                elif len(self._row_cells) == 2:
                    self.moods[self.current_mood][self.current_tense].append(
                        (self._row_cells[0][1], self._row_cells[1][1])
                    )

        elif tag == "table":
            if self._in_table_verbs:
                self._in_table_verbs = False
                self.current_tense = None
            if self._in_non_conj_table:
                self._in_non_conj_table = False


class LingoliaScraper:
    """
    Lingolia Français scraper implementing standard library HTTP requests,
    session cookie management, CSRF request token extraction, conjugation parsing,
    and live autocomplete suggestions.
    """

    def __init__(self):
        self._cookie_jar = http.cookiejar.CookieJar()
        self._token: Optional[str] = None
        self._opener = self._build_opener()

    def _build_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with certifi fallback when available."""
        try:
            import certifi
            return ssl.create_default_context(cafile=certifi.where())
        except Exception:
            try:
                return ssl.create_default_context()
            except Exception:
                return ssl._create_unverified_context()

    def _build_opener(self) -> urllib.request.OpenerDirector:
        """Build urllib opener with cookie support and custom SSL context."""
        ssl_ctx = self._build_ssl_context()
        https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
        cookie_processor = urllib.request.HTTPCookieProcessor(self._cookie_jar)
        return urllib.request.build_opener(cookie_processor, https_handler)

    def _ensure_session_and_token(self, force_refresh: bool = False) -> str:
        """
        Retrieves a valid REQUEST_TOKEN from Lingolia.
        If force_refresh is True or token is missing, fetches the conjugator landing page.
        """
        if self._token and not force_refresh:
            return self._token

        req = urllib.request.Request(
            CONJUGATOR_URL,
            headers={"User-Agent": USER_AGENT}
        )
        try:
            resp = self._opener.open(req, timeout=15)
            html = resp.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as e:
            # Fallback for environments with certificate validation hurdles
            if "CERTIFICATE_VERIFY_FAILED" in str(e):
                self._opener = urllib.request.build_opener(
                    urllib.request.HTTPCookieProcessor(self._cookie_jar),
                    urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
                )
                resp = self._opener.open(req, timeout=15)
                html = resp.read().decode("utf-8", errors="replace")
            else:
                raise

        token_m = re.search(
            r'name=["\']REQUEST_TOKEN["\']\s+value=["\']([a-f0-9]+)["\']',
            html,
            re.I
        )
        if not token_m:
            raise RuntimeError("Could not find REQUEST_TOKEN on Lingolia landing page.")

        self._token = token_m.group(1)
        return self._token

    def normalize_verb(self, verb: str) -> str:
        """Public normalizer method."""
        return normalize_verb(verb)

    def _fetch_verb_html(self, verb: str) -> str:
        """
        Performs POST request with the required form fields to retrieve verb HTML.
        """
        token = self._ensure_session_and_token()
        post_fields = {
            "FORM_SUBMIT": "",
            "REQUEST_TOKEN": token,
            "search_verb[input]": verb,
            "search_verb[force]": "",
            "verb": "",
            "search_verb[language]": "francais",
        }
        post_data = urllib.parse.urlencode(post_fields).encode("utf-8")
        req = urllib.request.Request(
            CONJUGATOR_URL,
            data=post_data,
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

        try:
            resp = self._opener.open(req, timeout=15)
            html = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 419):
                # Token might have expired, refresh once
                token = self._ensure_session_and_token(force_refresh=True)
                post_fields["REQUEST_TOKEN"] = token
                post_data = urllib.parse.urlencode(post_fields).encode("utf-8")
                req = urllib.request.Request(
                    CONJUGATOR_URL,
                    data=post_data,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Content-Type": "application/x-www-form-urlencoded",
                    }
                )
                resp = self._opener.open(req, timeout=15)
                html = resp.read().decode("utf-8", errors="replace")
            else:
                raise

        # Check if response provides a refreshed REQUEST_TOKEN
        new_token_m = re.search(
            r'name=["\']REQUEST_TOKEN["\']\s+value=["\']([a-f0-9]+)["\']',
            html,
            re.I
        )
        if new_token_m:
            self._token = new_token_m.group(1)

        return html

    def _deduce_auxiliary(
        self,
        verb_norm: str,
        moods: Dict[str, Dict[str, List[Tuple[str, str]]]],
        explicit_aux: Optional[str]
    ) -> str:
        """
        Determines the auxiliary verb ('avoir' or 'être').
        Uses explicit non-conjugated table value if present, otherwise deduces
        from compound tenses (e.g. Passé Composé) or reflexive nature.
        """
        if explicit_aux and explicit_aux.strip():
            val = explicit_aux.strip().lower()
            if "être" in val or "etre" in val:
                return "être"
            if "avoir" in val:
                return "avoir"

        # Reflexive verbs strictly conjugate with être in French
        if verb_norm.startswith(("se ", "s'", "s’")):
            return "être"

        # Check compound tenses in parsed moods (Passé Composé, Passé, etc.)
        etre_tokens = {"suis", "es", "est", "sommes", "êtes", "sont", "serai", "étais", "fus"}
        avoir_tokens = {"ai", "as", "a", "avons", "avez", "ont", "aurai", "avais", "eus"}

        for mood_dict in moods.values():
            for tense_name, rows in mood_dict.items():
                if "passé" in tense_name.lower():
                    for _, verb_form in rows:
                        tokens = verb_form.replace("’", "'").split()
                        for tok in tokens:
                            if tok in etre_tokens:
                                return "être"
                            if tok in avoir_tokens:
                                return "avoir"

        return "avoir"

    def _parse_conjugation_html(
        self,
        html_content: str,
        verb_norm: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validates Lingolia response and extracts structured conjugation dictionary.
        Returns None if verb is invalid or missing.
        """
        # Validate VerbData JavaScript object
        verb_data_m = re.search(r"var\s+VerbData\s*=\s*({.*?});", html_content, re.DOTALL)
        if not verb_data_m:
            return None

        verb_data_str = verb_data_m.group(1).strip()
        # Empty object var VerbData={}; indicates invalid / not found verb
        if re.sub(r"\s+", "", verb_data_str) == "{}":
            return None

        parser = LingoliaHTMLParser()
        parser.feed(html_content)

        non_conj = parser.non_conjugated
        moods = parser.moods

        # If no moods were parsed, treat as invalid
        if not moods:
            return None

        infinitif = non_conj.get("infinitif", verb_norm)
        participe_present = non_conj.get("participe_present", "")
        participe_passe = non_conj.get("participe_passe", "")
        auxiliaire = self._deduce_auxiliary(verb_norm, moods, non_conj.get("auxiliaire"))

        non_conj["infinitif"] = infinitif
        non_conj["participe_present"] = participe_present
        non_conj["participe_passe"] = participe_passe
        non_conj["auxiliaire"] = auxiliaire

        result: Dict[str, Any] = {
            "verb": verb_norm,
            "infinitif": infinitif,
            "participe_present": participe_present,
            "participe_passe": participe_passe,
            "auxiliaire": auxiliaire,
            "formes_non_conjuguees": non_conj,
            "moods": moods,
            # Top-level direct mood access
            "Indicatif": moods.get("Indicatif", {}),
            "Conditionnel": moods.get("Conditionnel", {}),
            "Subjonctif": moods.get("Subjonctif", {}),
            "Impératif": moods.get("Impératif", {}),
            "url": f"{CONJUGATOR_URL}?verb={urllib.parse.quote(verb_norm)}",
        }
        return result

    @functools.lru_cache(maxsize=512)
    def get_conjugation(self, verb: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves full conjugation data for a verb with LRU caching.
        Returns None if verb is empty or not found on Lingolia.
        """
        verb_norm = self.normalize_verb(verb)
        if not verb_norm:
            return None

        try:
            html = self._fetch_verb_html(verb_norm)
            return self._parse_conjugation_html(html, verb_norm)
        except Exception:
            return None

    @functools.lru_cache(maxsize=512)
    def autocomplete(self, query: str) -> List[str]:
        """
        Queries Lingolia's live autocomplete endpoint for matching verbs.
        Includes automatic fallback for reflexive prefixes ('se ', 's'').
        Cached with LRU cache (maxsize=512).
        """
        q = self.normalize_verb(query)
        if not q:
            return []

        def _do_query(search_term: str) -> Tuple[List[str], Optional[str]]:
            token = self._ensure_session_and_token()
            post_fields = {
                "verb": search_term,
                "action": "fmd",
                "id": "104",
                "lang": "francais",
                "REQUEST_TOKEN": token,
            }
            post_data = urllib.parse.urlencode(post_fields).encode("utf-8")
            req = urllib.request.Request(
                CONJUGATOR_URL,
                data=post_data,
                headers={
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Requested-With": "XMLHttpRequest",
                }
            )
            try:
                resp = self._opener.open(req, timeout=10)
                raw_json = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw_json)
                items = data.get("content", []) if isinstance(data, dict) else []
                new_token = data.get("token") if isinstance(data, dict) else None
                return items, new_token
            except Exception:
                return [], None

        results, new_token = _do_query(q)
        if new_token:
            self._token = new_token

        if results:
            return results

        # If empty and query had a reflexive prefix ('se ' or 's\''), try base verb
        is_reflexive = False
        base_term = q
        if q.startswith("se "):
            is_reflexive = True
            base_term = q[3:].strip()
        elif q.startswith(("s'", "s’")):
            is_reflexive = True
            base_term = q[2:].strip()

        if is_reflexive and base_term:
            base_results, new_token2 = _do_query(base_term)
            if new_token2:
                self._token = new_token2

            vowels = "aeiouyhéèêëàâîïôùû"
            formatted = []
            for item in base_results:
                if item and item[0].lower() in vowels:
                    formatted.append(f"s'{item}")
                else:
                    formatted.append(f"se {item}")
            return formatted

        return []


# Default module-level instance and convenience exports
_DEFAULT_SCRAPER = LingoliaScraper()


def get_conjugation(verb: str) -> Optional[Dict[str, Any]]:
    """Module-level convenience function for get_conjugation."""
    return _DEFAULT_SCRAPER.get_conjugation(verb)


def autocomplete(query: str) -> List[str]:
    """Module-level convenience function for autocomplete."""
    return _DEFAULT_SCRAPER.autocomplete(query)
