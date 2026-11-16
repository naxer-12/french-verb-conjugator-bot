"""
Telegram Bot Engine for French Verb Conjugation.
Powered by python-telegram-bot and Lingolia French Scraper Engine.

Features:
- Instant French verb conjugation across all 4 moods (Indicatif, Conditionnel, Subjonctif, Impératif)
- Non-conjugated forms (infinitif, participe présent, participe passé, auxiliaire)
- Clean monospaced column alignment for subjects and verb stems
- Interactive inline keyboards with active tab markers (✅ vs 🔸)
- Safe message chunking for "Tout afficher" (respecting Telegram's 4,096 char limit)
- Fallback spelling suggestions via Lingolia autocomplete
- Inline query mode (@bot <verb>) for live searching in any chat
"""

import asyncio
import html
import logging
import os
import re
from typing import Any, Dict, List, Optional
import urllib.parse

from dotenv import load_dotenv
import telegram
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

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

logger = logging.getLogger(__name__)

# UI constants
DIVIDER = "━━━━━━━━━━━━━━━━━━━━"
SUPPORTED_MOODS = ["Indicatif", "Conditionnel", "Subjonctif", "Impératif"]
DEFAULT_LINGOLIA_URL = "https://francais.lingolia.com/en/grammar/conjugator"

# Global scraper instance
_SCRAPER: Optional[LingoliaScraper] = None


def get_scraper() -> LingoliaScraper:
    """Returns singleton LingoliaScraper instance."""
    global _SCRAPER
    if _SCRAPER is None:
        _SCRAPER = LingoliaScraper()
    return _SCRAPER


def set_scraper(scraper: LingoliaScraper) -> None:
    """Sets the scraper instance (useful for testing or mocking)."""
    global _SCRAPER
    _SCRAPER = scraper


def get_bot_token() -> str:
    """
    Retrieves TELEGRAM_BOT_TOKEN from environment or .env file.
    Raises ValueError if missing, empty, or placeholder.
    """
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token == "your_telegram_bot_token_here":
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is missing or not configured in environment or .env file."
        )
    return token


def format_conjugation_message(data: Dict[str, Any], mood: str = "Indicatif") -> str:
    """
    Formats verb conjugation data into a Telegram HTML message for the specified mood.

    Structure:
    📖 <b>CONJUGAISON : <VERB_UPPER></b>
    ━━━━━━━━━━━━━━━━━━━━
    📌 <b>Formes non conjuguées</b>
    • <b>Infinitif :</b> ...
    • <b>Participe présent :</b> ...
    • <b>Participe passé :</b> ...
    • <b>Auxiliaire :</b> ...
    ━━━━━━━━━━━━━━━━━━━━
    🔹 <b>MODE <MOOD_UPPER></b>

    🕒 <b><TENSE_NAME></b>
    <code><subject_padded>  <verb_form></code>
    """
    if not data:
        return ""

    infinitif = data.get("infinitif") or data.get("verb") or ""
    inf_upper = html.escape(infinitif.upper(), quote=False)
    inf_escaped = html.escape(infinitif, quote=False)
    ppres_escaped = html.escape(data.get("participe_present") or "-", quote=False)
    ppas_escaped = html.escape(data.get("participe_passe") or "-", quote=False)
    aux_escaped = html.escape(data.get("auxiliaire") or "-", quote=False)

    lines: List[str] = [
        f"📖 <b>CONJUGAISON : {inf_upper}</b>",
        DIVIDER,
        "📌 <b>Formes non conjuguées</b>",
        f"• <b>Infinitif :</b> {inf_escaped}",
        f"• <b>Participe présent :</b> {ppres_escaped}",
        f"• <b>Participe passé :</b> {ppas_escaped}",
        f"• <b>Auxiliaire :</b> {aux_escaped}",
        DIVIDER,
        f"🔹 <b>MODE {html.escape(mood.upper(), quote=False)}</b>",
    ]

    mood_dict = data.get("moods", {}).get(mood) or data.get(mood, {})
    if not mood_dict:
        lines.append(f"\n<i>Aucune conjugaison disponible pour le mode {html.escape(mood, quote=False)}.</i>")
        return "\n".join(lines)

    for tense_name, rows in mood_dict.items():
        lines.append(f"\n🕒 <b>{html.escape(tense_name, quote=False)}</b>")
        if rows:
            max_sub_len = max([len(s) for s, _ in rows] + [8])
            for subject, verb_form in rows:
                padded_sub = (subject or "").ljust(max_sub_len)
                escaped_sub = html.escape(padded_sub, quote=False)
                escaped_verb = html.escape(verb_form or "", quote=False)
                lines.append(f"<code>{escaped_sub}  {escaped_verb}</code>")

    return "\n".join(lines)


def _format_mood_block(data: Dict[str, Any], mood: str) -> str:
    """Helper to format a single mood block with tenses and aligned rows."""
    mood_dict = data.get("moods", {}).get(mood) or data.get(mood, {})
    if not mood_dict:
        return ""

    lines: List[str] = [
        DIVIDER,
        f"🔹 <b>MODE {html.escape(mood.upper(), quote=False)}</b>",
    ]
    for tense_name, rows in mood_dict.items():
        lines.append(f"\n🕒 <b>{html.escape(tense_name, quote=False)}</b>")
        if rows:
            max_sub_len = max([len(s) for s, _ in rows] + [8])
            for subject, verb_form in rows:
                padded_sub = (subject or "").ljust(max_sub_len)
                escaped_sub = html.escape(padded_sub, quote=False)
                escaped_verb = html.escape(verb_form or "", quote=False)
                lines.append(f"<code>{escaped_sub}  {escaped_verb}</code>")

    return "\n".join(lines)


def format_all_moods(data: Dict[str, Any]) -> List[str]:
    """
    Formats all conjugation moods into Telegram-compatible HTML messages.
    If the combined text exceeds 3,800 characters, partitions cleanly along
    mood boundaries into Part 1 and Part 2 (e.g. Indicatif in Part 1,
    Conditionnel + Subjonctif + Impératif in Part 2) without breaking HTML tags.
    """
    if not data:
        return []

    infinitif = data.get("infinitif") or data.get("verb") or ""
    inf_upper = html.escape(infinitif.upper(), quote=False)
    inf_escaped = html.escape(infinitif, quote=False)
    ppres_escaped = html.escape(data.get("participe_present") or "-", quote=False)
    ppas_escaped = html.escape(data.get("participe_passe") or "-", quote=False)
    aux_escaped = html.escape(data.get("auxiliaire") or "-", quote=False)

    non_conj_lines = [
        DIVIDER,
        "📌 <b>Formes non conjuguées</b>",
        f"• <b>Infinitif :</b> {inf_escaped}",
        f"• <b>Participe présent :</b> {ppres_escaped}",
        f"• <b>Participe passé :</b> {ppas_escaped}",
        f"• <b>Auxiliaire :</b> {aux_escaped}",
    ]
    non_conj_block = "\n".join(non_conj_lines)

    # Gather all mood blocks in standard order
    all_moods = data.get("moods", {})
    extra_moods = [m for m in all_moods if m not in SUPPORTED_MOODS]
    ordered_moods = SUPPORTED_MOODS + extra_moods

    mood_blocks: Dict[str, str] = {}
    for mood in ordered_moods:
        block = _format_mood_block(data, mood)
        if block:
            mood_blocks[mood] = block

    header_single = f"📖 <b>CONJUGAISON : {inf_upper}</b>"
    full_text = header_single + "\n" + non_conj_block + ("\n" + "\n".join(mood_blocks.values()) if mood_blocks else "")

    if len(full_text) <= 3800:
        return [full_text]

    # Partition along mood boundaries: Indicatif in Part 1, others in Part 2
    p1_moods = ["Indicatif"]
    p2_moods = [m for m in ordered_moods if m != "Indicatif"]

    p1_blocks = [mood_blocks[m] for m in p1_moods if m in mood_blocks]
    p2_blocks = [mood_blocks[m] for m in p2_moods if m in mood_blocks]

    header_p1 = f"📖 <b>CONJUGAISON : {inf_upper} (Partie 1/2)</b>"
    p1_text = header_p1 + "\n" + non_conj_block + ("\n" + "\n".join(p1_blocks) if p1_blocks else "")

    header_p2 = f"📖 <b>CONJUGAISON : {inf_upper} (Partie 2/2)</b>"
    p2_text = header_p2 + ("\n" + "\n".join(p2_blocks) if p2_blocks else "")

    if len(p1_text) <= 3800 and len(p2_text) <= 3800:
        return [p1_text, p2_text]

    # Greedy multi-chunk fallback if any part still exceeds 3800 (for massive synthetic data)
    chunks: List[str] = []
    base_header = f"📖 <b>CONJUGAISON : {inf_upper}"
    curr_text = base_header + "</b>\n" + non_conj_block
    for block in mood_blocks.values():
        if len(curr_text) + len(block) + 1 <= 3800:
            curr_text += "\n" + block
        else:
            chunks.append(curr_text)
            curr_text = base_header + "</b>\n" + block
    if curr_text:
        chunks.append(curr_text)

    if len(chunks) > 1:
        total = len(chunks)
        final_chunks: List[str] = []
        for i, c in enumerate(chunks, 1):
            labeled = c.replace(base_header + "</b>", f"{base_header} (Partie {i}/{total})</b>", 1)
            final_chunks.append(labeled)
        return final_chunks
    return chunks


def build_conjugation_keyboard(
    verb: str, active_mood: str = "Indicatif", url: Optional[str] = None
) -> InlineKeyboardMarkup:
    """
    Builds the interactive inline keyboard with tab buttons for the 4 moods,
    'Tout afficher', and external link to Lingolia.
    Active tab is marked with '✅ <Mood>', inactive with '🔸 <Mood>'.
    """
    clean_verb = normalize_verb(verb)
    lingolia_url = url or f"{DEFAULT_LINGOLIA_URL}?verb={urllib.parse.quote(clean_verb)}"

    def btn_label(m: str) -> str:
        prefix = "✅" if active_mood.lower() == m.lower() else "🔸"
        return f"{prefix} {m}"

    row1 = [
        InlineKeyboardButton(
            text=btn_label("Indicatif"),
            callback_data=f"tab:{clean_verb}:Indicatif",
        ),
        InlineKeyboardButton(
            text=btn_label("Conditionnel"),
            callback_data=f"tab:{clean_verb}:Conditionnel",
        ),
    ]

    row2 = [
        InlineKeyboardButton(
            text=btn_label("Subjonctif"),
            callback_data=f"tab:{clean_verb}:Subjonctif",
        ),
        InlineKeyboardButton(
            text=btn_label("Impératif"),
            callback_data=f"tab:{clean_verb}:Impératif",
        ),
    ]

    row3 = [
        InlineKeyboardButton(
            text="📚 Tout afficher",
            callback_data=f"all:{clean_verb}",
        ),
        InlineKeyboardButton(
            text="🌐 Lingolia",
            url=lingolia_url,
        ),
    ]

    return InlineKeyboardMarkup([row1, row2, row3])


def build_suggestions_keyboard(suggestions: List[str]) -> InlineKeyboardMarkup:
    """
    Builds an inline keyboard offering autocomplete suggestions when a verb is not found.
    """
    keyboard: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []
    for s in suggestions[:8]:
        btn = InlineKeyboardButton(text=s, callback_data=f"conj:{s}")
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def format_not_found_message(verb: str, has_suggestions: bool = False) -> str:
    """Formats an informative error message when a verb is not found in Lingolia."""
    escaped_verb = html.escape(verb, quote=False)
    if has_suggestions:
        return (
            f"⚠️ <i>Verbe « {escaped_verb} » non trouvé.</i>\n\n"
            "Lingolia attend la forme <b>infinitif</b>. Vouliez-vous dire :"
        )
    return (
        f"⚠️ <i>Verbe « {escaped_verb} » non trouvé.</i>\n\n"
        "Lingolia attend la forme <b>infinitif</b> (ex: <i>parler</i>, <i>finir</i>, <i>s'appeler</i>).\n"
        "Vérifiez l'orthographe du verbe et réessayez."
    )


# ---------------------------------------------------------------------------
# Telegram Handlers
# ---------------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcomes the user and explains bot usage."""
    if not update.message:
        return
    bot_name = context.bot.username if context.bot and context.bot.username else "verb_conjugator_bot"
    welcome_text = (
        "🇫🇷 <b>Bienvenue sur le Bot Conjugueur de Verbes Français !</b>\n"
        f"{DIVIDER}\n"
        "Ce bot conjugue instantanément n'importe quel verbe français à tous les modes "
        "et temps, avec ses formes non conjuguées et son auxiliaire (avoir / être).\n\n"
        "📌 <b>Comment l'utiliser :</b>\n"
        "• <b>Texte direct :</b> Envoyez simplement un verbe (ex: <code>parler</code>, <code>être</code>, <code>s'appeler</code>)\n"
        "• <b>Commande :</b> Utilisez <code>/conj &lt;verbe&gt;</code> (ex: <code>/conj aller</code>)\n"
        f"• <b>Mode Inline :</b> Tapez <code>@{bot_name} &lt;verbe&gt;</code> dans n'importe quel chat pour partager une conjugaison !\n"
        "• <b>Navigation interactive :</b> Utilisez les boutons sous chaque message pour changer de mode ou tout afficher.\n\n"
        "💡 <i>Envoyez un verbe dès maintenant pour essayer !</i>"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays comprehensive help guide."""
    if not update.message:
        return
    bot_name = context.bot.username if context.bot and context.bot.username else "verb_conjugator_bot"
    help_text = (
        "📖 <b>Aide & Guide d'Utilisation</b>\n"
        f"{DIVIDER}\n"
        "🔹 <b>Commandes disponibles :</b>\n"
        "• <code>/start</code> : Afficher le message d'accueil\n"
        "• <code>/help</code> : Afficher ce guide d'aide\n"
        "• <code>/conj &lt;verbe&gt;</code> : Conjuguer un verbe français\n\n"
        "🔹 <b>Modes pris en charge :</b>\n"
        "• <b>Indicatif</b> (Présent, Passé composé, Imparfait, Plus-que-parfait, Passé simple, Futur simple, etc.)\n"
        "• <b>Conditionnel</b> (Présent, Passé)\n"
        "• <b>Subjonctif</b> (Présent, Passé, Imparfait, Plus-que-parfait)\n"
        "• <b>Impératif</b> (Présent)\n\n"
        "🔹 <b>Navigation par boutons :</b>\n"
        "• <code>[ Indicatif ]</code>, <code>[ Conditionnel ]</code>, etc. : Basculez d'onglet instantanément\n"
        "• <code>[ 📚 Tout afficher ]</code> : Affiche l'intégralité des modes découpés proprement\n"
        "• <code>[ 🌐 Lingolia ]</code> : Fiche officielle Lingolia\n\n"
        f"🔹 <b>Mode Inline direct :</b>\n"
        f"Tapez <code>@{bot_name} &lt;recherche&gt;</code> dans n'importe quelle discussion pour autocompléter et envoyer la conjugaison directement !"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


async def handle_verb_lookup(message: telegram.Message, verb_input: str) -> None:
    """Central lookup logic for plain text and /conj command."""
    scraper = get_scraper()
    verb_norm = normalize_verb(verb_input)
    if not verb_norm:
        await message.reply_text(
            "⚠️ Veuillez préciser un verbe valide à conjuguer.\n<i>Exemple :</i> <code>/conj parler</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    data = await asyncio.to_thread(scraper.get_conjugation, verb_norm)
    if data:
        text = format_conjugation_message(data, mood="Indicatif")
        keyboard = build_conjugation_keyboard(verb_norm, active_mood="Indicatif", url=data.get("url"))
        await message.reply_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        # Fallback to autocomplete suggestions
        suggestions = await asyncio.to_thread(scraper.autocomplete, verb_norm)
        if suggestions:
            not_found_text = format_not_found_message(verb_norm, has_suggestions=True)
            keyboard = build_suggestions_keyboard(suggestions)
            await message.reply_text(text=not_found_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        else:
            not_found_text = format_not_found_message(verb_norm, has_suggestions=False)
            await message.reply_text(text=not_found_text, parse_mode=ParseMode.HTML)


async def conj_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /conj <verb> command."""
    if not update.message:
        return
    if not context.args:
        await update.message.reply_text(
            "⚠️ Veuillez préciser un verbe.\n<i>Exemple :</i> <code>/conj parler</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    verb_query = " ".join(context.args)
    await handle_verb_lookup(update.message, verb_query)


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles any non-command plain text message as a French verb lookup."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if not text or text.startswith("/"):
        return
    await handle_verb_lookup(update.message, text)


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles interactive callback queries:
    - tab:<verb>:<mood> -> instant mood tab switching
    - all:<verb> -> sends all moods chunked safely
    - conj:<verb> -> conjugating a suggested verb
    """
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    scraper = get_scraper()

    if data.startswith("tab:"):
        parts = data.split(":", 2)
        if len(parts) == 3:
            _, verb, mood = parts
            conj_data = await asyncio.to_thread(scraper.get_conjugation, verb)
            if not conj_data:
                await query.answer("Verbe introuvable sur Lingolia.", show_alert=True)
                return

            new_text = format_conjugation_message(conj_data, mood=mood)
            new_kb = build_conjugation_keyboard(verb, active_mood=mood, url=conj_data.get("url"))

            try:
                await query.edit_message_text(text=new_text, reply_markup=new_kb, parse_mode=ParseMode.HTML)
            except telegram.error.BadRequest as e:
                if "Message is not modified" not in str(e):
                    logger.warning("Could not edit message text on tab switch: %s", e)
            await query.answer(f"Mode {mood}")

    elif data.startswith("all:"):
        parts = data.split(":", 1)
        if len(parts) == 2:
            _, verb = parts
            conj_data = await asyncio.to_thread(scraper.get_conjugation, verb)
            if not conj_data:
                await query.answer("Verbe introuvable sur Lingolia.", show_alert=True)
                return

            chunks = format_all_moods(conj_data)
            await query.answer("Affichage de tous les modes...")
            if query.message:
                for chunk in chunks:
                    await query.message.reply_text(chunk, parse_mode=ParseMode.HTML)
            elif query.inline_message_id:
                try:
                    await query.edit_message_text(text=chunks[0], parse_mode=ParseMode.HTML)
                except telegram.error.BadRequest as e:
                    if "Message is not modified" not in str(e):
                        logger.warning("Could not edit inline message: %s", e)

    elif data.startswith("conj:"):
        parts = data.split(":", 1)
        if len(parts) == 2:
            _, verb = parts
            conj_data = await asyncio.to_thread(scraper.get_conjugation, verb)
            if not conj_data:
                await query.answer("Verbe introuvable sur Lingolia.", show_alert=True)
                return

            text = format_conjugation_message(conj_data, mood="Indicatif")
            kb = build_conjugation_keyboard(verb, active_mood="Indicatif", url=conj_data.get("url"))

            try:
                await query.edit_message_text(text=text, reply_markup=kb, parse_mode=ParseMode.HTML)
            except telegram.error.BadRequest:
                if query.message:
                    await query.message.reply_text(text=text, reply_markup=kb, parse_mode=ParseMode.HTML)
            await query.answer(f"Conjugaison de {verb}")


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles live inline mode (@bot <query>):
    Provides live autocomplete suggestions; tapping any result sends the full
    Indicatif conjugation view with interactive navigation keyboard.
    """
    inline_query = update.inline_query
    if not inline_query:
        return

    query_str = inline_query.query.strip()
    scraper = get_scraper()

    if not query_str:
        candidates = ["être", "avoir", "aller", "faire", "parler", "prendre", "pouvoir", "vouloir"]
    else:
        candidates = await asyncio.to_thread(scraper.autocomplete, query_str)
        norm_q = normalize_verb(query_str)
        if norm_q and norm_q not in candidates:
            candidates = [norm_q] + candidates

    # Return top results (up to 10)
    candidates = candidates[:10]

    if not candidates:
        await inline_query.answer([], cache_time=300)
        return

    tasks = [asyncio.to_thread(scraper.get_conjugation, c) for c in candidates]
    data_results = await asyncio.gather(*tasks, return_exceptions=True)

    results: List[InlineQueryResultArticle] = []
    for idx, (verb, data) in enumerate(zip(candidates, data_results)):
        article_id = f"conj_{verb}_{idx}"
        if isinstance(data, dict) and data:
            msg_text = format_conjugation_message(data, mood="Indicatif")
            kb = build_conjugation_keyboard(verb, active_mood="Indicatif", url=data.get("url"))
            ppas = data.get("participe_passe", "")
            aux = data.get("auxiliaire", "")
            desc = f"Participe: {ppas} • Auxiliaire: {aux} | Appuyez pour voir la conjugaison complète"
        else:
            msg_text = (
                f"📖 <b>CONJUGAISON : {html.escape(verb.upper(), quote=False)}</b>\n\n"
                "<i>Cliquez ci-dessous pour charger la conjugaison complète :</i>"
            )
            kb = InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="📖 Conjuguer", callback_data=f"conj:{verb}")]]
            )
            desc = "Appuyez pour voir la conjugaison complète"

        article = InlineQueryResultArticle(
            id=article_id,
            title=verb,
            description=desc,
            input_message_content=InputTextMessageContent(
                message_text=msg_text,
                parse_mode=ParseMode.HTML,
            ),
            reply_markup=kb,
        )
        results.append(article)

    await inline_query.answer(results, cache_time=300)


# ---------------------------------------------------------------------------
# Application Initialization & Entry Point
# ---------------------------------------------------------------------------

async def start_health_server(app: Application) -> None:
    """
    Starts a minimal async HTTP health check server if the PORT environment variable
    is defined (automatically provided by cloud platforms like Render).
    Allows running the bot as a free Render Web Service.
    """
    port_str = os.getenv("PORT")
    if not port_str:
        return

    try:
        port = int(port_str)
    except ValueError:
        port = 10000

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await reader.readline()
            body = b"OK - French Verb Conjugator Bot is running!\n"
            header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/plain; charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"Connection: close\r\n\r\n"
            ).encode("utf-8")
            writer.write(header + body)
            await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    try:
        server = await asyncio.start_server(handle_client, "0.0.0.0", port)
        logger.info("Health check HTTP server started on 0.0.0.0:%d (Render compatible)", port)
        app.bot_data["health_server"] = server
    except Exception as e:
        logger.warning("Could not start health check HTTP server on port %d: %s", port, e)


def build_application(token: Optional[str] = None) -> Application:
    """
    Builds and configures the Telegram Application with all command,
    message, callback, and inline handlers.
    """
    if token is None:
        token = get_bot_token()

    request = HTTPXRequest(
        connect_timeout=20.0,
        read_timeout=20.0,
        write_timeout=20.0,
        pool_timeout=20.0,
    )
    app = (
        Application.builder()
        .token(token)
        .request(request)
        .post_init(start_health_server)
        .build()
    )

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("conj", conj_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    app.add_handler(InlineQueryHandler(inline_query_handler))

    return app


def main() -> None:
    """Main execution loop for the Telegram bot."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logger.info("Initializing French Verb Conjugator Bot...")

    try:
        app = build_application()
        logger.info("Bot starting polling loop. Press Ctrl+C to stop.")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical("Fatal error running bot: %s", e)
        raise


if __name__ == "__main__":
    main()
