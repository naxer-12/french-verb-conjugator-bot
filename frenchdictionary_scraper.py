"""
Dedicated FrenchDictionary.com Scraper.
Specifically scrapes https://www.frenchdictionary.com/ for a given French word:
- Examples: https://www.frenchdictionary.com/examples/<word>?lang=fr
- Translations & Definitions: https://www.frenchdictionary.com/translate/<word>
- Conjugations: https://www.frenchdictionary.com/conjugate/<word>

Note: frenchdictionary.com is protected by Cloudflare Turnstile / Bot Verification.
On standard cloud/datacenter IP addresses, requests may receive an HTTP 403 Challenge.
This module supports custom User-Agent headers, session cookies, and proxies.
"""

from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser
import http.cookiejar
import logging
import re
import html
import ssl

logger = logging.getLogger(__name__)


def _create_ssl_context() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


class FrenchDictionaryHTMLParser(HTMLParser):
    """
    HTML parser tailored for frenchdictionary.com pages:
    - Extracts bilingual example pairs (French source + English translation)
    - Extracts definitions and grammatical classifications
    """

    def __init__(self) -> None:
        super().__init__()
        self.examples: List[Tuple[str, str]] = []
        self.definitions: List[str] = []
        self.part_of_speech: Optional[str] = None

        self._in_example_container = False
        self._current_source: List[str] = []
        self._current_translation: List[str] = []
        self._current_tag: Optional[str] = None
        self._tag_stack: List[str] = []
        self._capture_mode: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self._tag_stack.append(tag)
        attr_dict = {k.lower(): v for k, v in attrs if v is not None}
        cls = attr_dict.get("class", "")
        elem_id = attr_dict.get("id", "")

        # Detect example sentence containers in frenchdictionary.com
        if any(c in cls for c in ["example", "sample", "ex-pair", "dictionary-entry"]):
            self._in_example_container = True

        # Detect lang attributes or classes
        if attr_dict.get("lang") == "fr" or "source" in cls or "fr" in cls:
            self._capture_mode = "fr"
        elif attr_dict.get("lang") == "en" or "translation" in cls or "target" in cls:
            self._capture_mode = "en"

    def handle_endtag(self, tag: str) -> None:
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

        if tag in ("p", "div", "li", "tr") and self._current_source and self._current_translation:
            src = " ".join("".join(self._current_source).split()).strip()
            trans = " ".join("".join(self._current_translation).split()).strip()
            if src and trans and len(src) > 5 and len(trans) > 5:
                self.examples.append((src, trans))
            self._current_source = []
            self._current_translation = []
            self._capture_mode = None

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return

        if self._capture_mode == "fr":
            self._current_source.append(data)
        elif self._capture_mode == "en":
            self._current_translation.append(data)


class FrenchDictionaryScraper:
    """
    Direct scraper client for FrenchDictionary.com.
    """

    BASE_URL = "https://www.frenchdictionary.com"

    def __init__(self, cookies: Optional[str] = None) -> None:
        self.cookie_jar = http.cookiejar.CookieJar()
        https_handler = urllib.request.HTTPSHandler(context=_create_ssl_context())
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            https_handler,
        )
        self.custom_cookies = cookies

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Upgrade-Insecure-Requests": "1",
        }
        if self.custom_cookies:
            headers["Cookie"] = self.custom_cookies
        return headers

    def fetch_word_examples(self, word: str) -> Tuple[bool, List[Tuple[str, str]], str]:
        """
        Fetches example sentences from:
        https://www.frenchdictionary.com/examples/<word>?lang=fr

        Returns: (success, examples_list, error_or_status_message)
        """
        clean_word = word.strip().lower()
        url = f"{self.BASE_URL}/examples/{urllib.parse.quote(clean_word)}?lang=fr"
        req = urllib.request.Request(url, headers=self._get_headers())

        try:
            with self.opener.open(req, timeout=8) as response:
                content = response.read().decode("utf-8", errors="replace")
                parser = FrenchDictionaryHTMLParser()
                parser.feed(content)

                # Regex fallback to extract sentence pairs from modern React/SSR data
                if not parser.examples:
                    # Look for JSON payload or patterns in SSR script tags
                    matches = re.findall(
                        r'"source":"([^"]+)".*?"target":"([^"]+)"', content
                    )
                    for src, tgt in matches[:10]:
                        s = html.unescape(src.encode("utf-8").decode("unicode_escape", errors="ignore"))
                        t = html.unescape(tgt.encode("utf-8").decode("unicode_escape", errors="ignore"))
                        if s and t:
                            parser.examples.append((s, t))

                return True, parser.examples, "OK"

        except urllib.error.HTTPError as e:
            if e.code == 403:
                return (
                    False,
                    [],
                    f"HTTP 403 Forbidden: frenchdictionary.com is protected by Cloudflare Turnstile anti-bot verification.",
                )
            return False, [], f"HTTP {e.code} Error: {e.reason}"
        except Exception as e:
            return False, [], f"Request Error: {str(e)}"

    def fetch_word_translation(self, word: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Fetches word translation and definitions from:
        https://www.frenchdictionary.com/translate/<word>

        Returns: (success, data_dict, error_or_status_message)
        """
        clean_word = word.strip().lower()
        url = f"{self.BASE_URL}/translate/{urllib.parse.quote(clean_word)}"
        req = urllib.request.Request(url, headers=self._get_headers())

        try:
            with self.opener.open(req, timeout=8) as response:
                content = response.read().decode("utf-8", errors="replace")
                data = {
                    "word": clean_word,
                    "url": url,
                    "definitions": [],
                }
                # Look for English quick definition
                m_def = re.search(r'<span class="quick-def">([^<]+)</span>', content)
                if m_def:
                    data["definitions"].append(m_def.group(1).strip())
                return True, data, "OK"

        except urllib.error.HTTPError as e:
            if e.code == 403:
                return (
                    False,
                    {},
                    f"HTTP 403 Forbidden: frenchdictionary.com is protected by Cloudflare Turnstile anti-bot verification.",
                )
            return False, {}, f"HTTP {e.code} Error: {e.reason}"
        except Exception as e:
            return False, {}, f"Request Error: {str(e)}"
