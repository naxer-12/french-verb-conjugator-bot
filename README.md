# French Verb Conjugator Telegram Bot 🇫🇷📖

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-v21%2B-0088cc.svg)](https://core.telegram.org/bots/api)
[![Data Source](https://img.shields.io/badge/Data%20Source-Lingolia%20Fran%C3%A7ais-green.svg)](https://francais.lingolia.com/)
[![Tests](https://img.shields.io/badge/Unit%20Tests-34%20passed-brightgreen.svg)](test_bot_logic.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A high-performance, feature-complete Telegram bot (`@verb_conjugator_bot`) that conjugates any French verb across all moods and tenses. It replicates the complete feature set of **Lingolia Français** with instant inline keyboard navigation, live inline query autocomplete, safe message chunking, and intelligent typo/fallback suggestions.

Built with pure Python standard library scraping (`urllib`, `http.cookiejar`, `html.parser`), ensuring maximum speed, zero browser overhead, and rock-solid reliability.

---

## Table of Contents

- [Features](#features)
- [Bot Architecture & Data Model](#bot-architecture--data-model)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Local Setup](#installation--local-setup)
- [Configuration (.env)](#configuration-env)
- [Running Unit Tests](#running-unit-tests)
- [Running the Bot](#running-the-bot)
- [Telegram BotFather Configuration](#telegram-botfather-configuration)
  - [1. Creating the Bot & Obtaining Token](#1-creating-the-bot--obtaining-token)
  - [2. Setting Bot Commands (`/setcommands`)](#2-setting-bot-commands-setcommands)
  - [3. Enabling Inline Mode (`/setinline`)](#3-enabling-inline-mode-setinline)
  - [4. Description & About Text](#4-description--about-text)
- [Production Deployment Guides](#production-deployment-guides)
  - [Option A: Docker (Recommended)](#option-a-docker-recommended)
  - [Option B: Systemd Service (Linux VPS / Ubuntu / Debian)](#option-b-systemd-service-linux-vps--ubuntu--debian)
  - [Option C: Render (Cloud Worker)](#option-c-render-cloud-worker)
  - [Option D: Railway](#option-d-railway)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Pluggable Provider Architecture & FrenchDictionary.com Backend

This project features a pluggable conjugation & examples provider architecture:
- **`frenchdictionary` (Default on `feature/frenchdictionary-only`)**: Dedicated scraper targeting `https://www.frenchdictionary.com/examples/<word>?lang=fr` (e.g. `travailler`), `/translate/<word>`, and `/conjugate/<word>`.
- **`hybrid`**: Combines Lingolia scraping with curated student pedagogy, morphological inference, synonyms, and bilingual examples.
- **`lingolia`**: Direct Lingolia Français conjugator scraper.

### FrenchDictionary.com Dedicated Branch (`feature/frenchdictionary-only`)
On this branch, typing any word or using `/examples <word>` directly targets:
```
https://www.frenchdictionary.com/examples/<word>?lang=fr
```
- **Example Extraction**: Parses bilingual French/English sentence pairs (`FrenchDictionaryHTMLParser`).
- **Cloudflare Turnstile Handling**: When queried from datacenter/cloud IPs, `frenchdictionary.com` serves an `HTTP 403 Forbidden` anti-bot challenge (`cf-mitigated: challenge`). The bot transparently notifies the user, provides the direct clickable link to open the page in their browser, and presents the formatted educational study card.

---

## Features

- **⚡ Instant Conjugation**: Send any French verb as a plain message (e.g., `aller`, `finir`, `se lever`) or use `/conj <verbe>`.
- **🔍 Live Inline Autocomplete (`@verb_conjugation_bot <query>`)**: Type the bot handle in any private or group chat to receive instant live completion suggestions with English translations and verb details.
- **🎓 Bilingual Pedagogical Study Guide (`[ 🎓 Fiche Étudiant ]`)**:
  - English translation, French meaning, verb classification (1er, 2ème, 3ème groupe), and CEFR proficiency level (A1-B2).
  - Practical student study tips explaining irregular stems, silent endings (`-e, -es, -ent`), and auxiliary rules (`avoir` vs `être`).
  - Clear bilingual overview of the 4 grammatical moods.
- **💬 Synonyms & Bilingual Example Sentences (`[ 💬 Exemples & Synonymes ]`)**:
  - High-frequency French synonyms with contextual English glosses.
  - Numbered real-world example sentences across key tenses with side-by-side French and English translations.
- **📚 Complete Mood & Tense Coverage with Formative Tooltips**:
  - Every mood header displays a bilingual usage tooltip (e.g., *Factual & Objective / Réel & Factuel*).
  - Every tense displays its practical purpose (e.g., *Présent • Current actions & habits*, *Passé composé • Completed past actions*).
  - **Formes non conjuguées**: Infinitif, Participe passé, Participe présent, Auxiliaire.
  - **Indicatif**: Présent, Passé composé, Imparfait, Plus-que-parfait, Passé simple, Passé antérieur, Futur simple, Futur antérieur.
  - **Conditionnel**: Présent, Passé (1re forme).
  - **Subjonctif**: Présent, Passé, Imparfait, Plus-que-parfait.
  - **Impératif**: Présent.
- **🎛️ Interactive Inline Keyboard Tabs**: Switch moods or study tabs with one tap without re-scraping (`[ Indicatif ]`, `[ Conditionnel ]`, `[ Subjonctif ]`, `[ Impératif ]`, `[ 💬 Exemples & Synonymes ]`, `[ 🎓 Fiche Étudiant ]`). Active tab is visually badged with `✅`.
- **📜 "Tout afficher" (View All Moods)**: Displays all moods at once with automatic HTML-aware chunking respecting Telegram's 4,096 character limit.
- **✨ Monospaced Column Alignment**: Subjects and conjugated stems are neatly aligned in `<code>` blocks for optimal readability on both mobile and desktop screens.
- **🔄 Robust Input Normalization**: Automatically trims whitespace, lowers case, strips surrounding punctuation, normalizes typographic curly quotes (`’`, `‘` → `'`), and properly handles pronominal/reflexive verbs (`se laver`, `s'appeler`).
- **💡 Smart Fallback Suggestions**: If an inflected form, typo, or non-infinitive query is entered, the bot queries Lingolia's autocomplete endpoint and offers interactive suggestion buttons.
- **🚀 Zero-Overhead Scraper Engine**: Powered purely by standard library modules (`urllib.request`, `http.cookiejar`, `html.parser`), with dual-tier LRU caching (`@functools.lru_cache(maxsize=1024)`) for sub-millisecond responses on repeated queries.

---

## Bot Architecture & Data Model

```
┌────────────────────────────────────────────────────────┐
│                   Telegram Client                      │
│   (Direct Chat / Group / Inline Query @bot <verb>)     │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             python-telegram-bot (v21+)                 │
│  - CommandHandler (/start, /help, /conj)               │
│  - MessageHandler (Filters.TEXT & ~Filters.COMMAND)    │
│  - CallbackQueryHandler (tab switching, "all", conj)   │
│  - InlineQueryHandler (as-you-type autocomplete)       │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             Pluggable Provider Architecture            │
│                 (BaseConjugationProvider)              │
├──────────────────────────┬─────────────────────────────┤
│ • FrenchDictionary (Def.)│ frenchdictionary.com / Study│
│ • HybridProvider         │ Lingolia tables + Pedagogy  │
│ • LingoliaProvider       │ Pure Lingolia tables        │
└──────────────────────────┴─────────────────────────────┘
```

### Pluggable Providers
You can select the active conjugation and vocabulary engine via the `CONJUGATION_PROVIDER` environment variable:
- `CONJUGATION_PROVIDER=frenchdictionary` (Default): FrenchDictionary.com provider with direct website links, complete conjugation tables, bilingual English-French pedagogical engine, synonyms, and contextual example sentences.
- `CONJUGATION_PROVIDER=hybrid`: Uses Lingolia's conjugation tables combined with our bilingual English-French pedagogical engine, synonyms, and example sentences.
- `CONJUGATION_PROVIDER=lingolia`: Pure Lingolia Français scraper.

---

## Project Structure

```
french_verb_conjugator_bot/
├── .env                  # Local secret configuration (TELEGRAM_BOT_TOKEN)
├── .env.example          # Template for environment variables
├── .gitignore            # Git exclusion rules
├── __init__.py           # Package indicator
├── bot.py                # Main bot application and Telegram event handlers
├── lingolia.py           # Pure standard library Lingolia scraper & parser
├── pedagogy.py           # Bilingual student study guides, synonyms & examples
├── providers/            # Pluggable provider architecture
│   ├── base.py           # BaseConjugationProvider interface
│   ├── factory.py        # get_provider() factory
│   ├── hybrid_provider.py# Lingolia + Bilingual Pedagogy
│   ├── lingolia_provider.py
│   └── french_dictionary_provider.py
├── requirements.txt      # Production dependencies
├── Dockerfile            # Multi-platform container configuration
├── render.yaml           # 1-click Render blueprint specification
├── README.md             # Complete documentation and setup manual
├── test_scraper.py       # Unit tests for scraper, normalization & caching
├── test_bot_logic.py     # Unit tests for message formatting, chunking & handlers
└── test_providers.py     # Unit tests for pluggable providers
```

---

## Prerequisites

- **Python**: Version `3.9` or higher (`python3 --version`).
- **Telegram Account**: To interact with `@BotFather` and run the bot.
- **Git** (optional, for cloning).

---

## Installation & Local Setup

### 1. Clone or Navigate to the Directory
```bash
cd french_verb_conjugator_bot
```

### 2. Create and Activate a Virtual Environment
```bash
# On macOS / Linux
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Configuration (.env)

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` in your text editor and set your Telegram Bot token obtained from `@BotFather`:
```ini
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ123456789
```

> ⚠️ **Security Warning**: Never commit your real `.env` file or API tokens to GitHub. `.env` is ignored by default in `.gitignore`.

---

## Running Unit Tests

The test suite contains 23 comprehensive tests covering:
- Regular `-er`, irregular verbs (`avoir`, `être`, `aller`, `faire`), and reflexive verbs (`se lever`, `s'appeler`).
- Input normalization and curly apostrophes (`s’appeler`).
- Autocomplete endpoints and caching behavior.
- HTML escaping, monospaced table alignment, and safe chunking algorithm (< 3,800 characters per message).
- Inline keyboards and callback state markers (`✅` vs `🔸`).

Run the test suite from inside `french_verb_conjugator_bot`:
```bash
python3 -m unittest discover . -v
```

Or run from the project root:
```bash
python3 -m unittest discover french_verb_conjugator_bot -v
```

Expected output:
```text
Ran 23 tests in 8.3s
OK
```

---

## Running the Bot

Once `.env` is configured and dependencies are installed, start the bot:
```bash
python3 bot.py
```

Console output:
```text
INFO:bot:Starting French Verb Conjugator Bot (@verb_conjugator_bot)...
INFO:bot:Bot is polling for updates. Press Ctrl+C to stop.
```

Open Telegram, search for your bot, send `/start`, and type any verb (e.g. `parler`)!

---

## Telegram BotFather Configuration

To ensure your bot features official commands and live inline querying, configure it via Telegram's official `@BotFather`.

### 1. Creating the Bot & Obtaining Token
1. Open Telegram and search for `@BotFather`.
2. Send `/newbot`.
3. Choose a display name (e.g., `Conjugueur Français`).
4. Choose a unique username ending in `bot` (e.g., `french_verb_conjugator_bot`).
5. Copy the generated HTTP API token and paste it into your `.env` file under `TELEGRAM_BOT_TOKEN`.

### 2. Setting Bot Commands (`/setcommands`)
1. In `@BotFather`, send `/setcommands`.
2. Select your bot.
3. Paste the following command list:
```text
start - Démarrer le bot
help - Guide d'utilisation et commandes
conj - Conjuguer un verbe (ex: /conj aller)
```

### 3. Enabling Inline Mode (`/setinline`)
Inline Mode allows users to type `@your_bot_name <verb>` in any Telegram chat to get instant as-you-type conjugation suggestions.

1. In `@BotFather`, send `/setinline`.
2. Select your bot.
3. When asked for placeholder text, send:
```text
Tapez un verbe français... (ex: parler, être)
```
4. BotFather will confirm: `Success! Inline mode has been enabled in your bot.`

### 4. Description & About Text
- **Description** (shown on empty chat screen):
  - Send `/setdescription` -> Select bot ->
  ```text
  🇫🇷 Conjugueur de verbes français haute performance.
  Conjuguez n'importe quel verbe à tous les temps et modes (Indicatif, Conditionnel, Subjonctif, Impératif).
  Supporte le mode inline partout sur Telegram !
  ```
- **About Text** (shown on bot profile):
  - Send `/setabouttext` -> Select bot ->
  ```text
  Conjugueur de verbes français complet alimenté par Lingolia. Tapez un verbe ou utilisez @nom_du_bot en mode inline.
  ```

---

## Production Deployment Guides

### Option A: Docker (Recommended)

A lightweight multi-stage Dockerfile is included.

#### 1. Build the Docker Image
```bash
docker build -t french-verb-conjugator-bot .
```

#### 2. Run the Container
```bash
docker run -d \
  --name french-verb-bot \
  --restart unless-stopped \
  --env-file .env \
  french-verb-conjugator-bot
```

#### 3. View Logs & Container Status
```bash
docker logs -f french-verb-bot
docker ps
```

#### Optional: Docker Compose
Create a `docker-compose.yml` in the folder:
```yaml
version: '3.8'

services:
  conjugator-bot:
    build: .
    container_name: french-verb-conjugator-bot
    restart: unless-stopped
    env_file:
      - .env
```
Run with:
```bash
docker compose up -d
```

---

### Option B: Systemd Service (Linux VPS / Ubuntu / Debian)

Running the bot as a background systemd service ensures automatic restarts on crash or system reboot.

#### 1. Clone the repository on your server
```bash
sudo mkdir -p /opt/french-verb-bot
sudo chown -R $USER:$USER /opt/french-verb-bot
cp -r . /opt/french-verb-bot/
cd /opt/french-verb-bot
```

#### 2. Set up virtual environment and `.env`
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env   # Enter your TELEGRAM_BOT_TOKEN
```

#### 3. Create Systemd Service File
```bash
sudo nano /etc/systemd/system/french-verb-bot.service
```

Paste the following service definition (replace `ubuntu` with your server username):
```ini
[Unit]
Description=French Verb Conjugator Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/french-verb-bot
ExecStart=/opt/french-verb-bot/venv/bin/python bot.py
Restart=always
RestartSec=5
EnvironmentFile=/opt/french-verb-bot/.env

# Security hardening
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

#### 4. Enable and Start the Service
```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable french-verb-bot

# Start service now
sudo systemctl start french-verb-bot

# Check service status
sudo systemctl status french-verb-bot

# Inspect live logs
sudo journalctl -u french-verb-bot -f
```

---

### Option C: Render (Cloud Worker)

Render can run long-running background worker services.

1. Push your repository to GitHub or GitLab.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** -> **Background Worker**.
4. Connect your repository.
5. Fill in the settings:
   - **Name**: `french-verb-conjugator-bot`
   - **Environment**: `Python 3`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 bot.py`
6. Under **Environment Variables**, add:
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: `your_token_from_botfather`
7. Click **Create Background Worker**.

---

### Option D: Railway

1. Install the Railway CLI or connect via GitHub on [railway.app](https://railway.app/).
2. Create a **New Project** and deploy from your repository.
3. In service **Settings**:
   - Set **Start Command** to `python3 bot.py`.
4. In **Variables**:
   - Add `TELEGRAM_BOT_TOKEN = <your_token>`.
5. Railway will automatically detect Python, build the container, and start polling Telegram.

---

## Troubleshooting

### Bot does not respond to inline queries (`@bot <verb>`)
- Ensure you executed `/setinline` on `@BotFather` as described in [Enabling Inline Mode](#3-enabling-inline-mode-setinline).
- If recently enabled, Telegram desktop/mobile apps may cache inline settings for up to a few minutes; restart your Telegram client if necessary.

### `ValueError: TELEGRAM_BOT_TOKEN is missing or not configured`
- Check that your `.env` file exists in the directory where `bot.py` is being executed.
- Make sure the token does not equal the default placeholder string `"your_telegram_bot_token_here"`.

### HTTP Errors or Timeouts when Fetching Conjugations
- The bot includes polite User-Agent headers and standard cookie jars. Check your server's outbound internet connectivity with `curl -I https://francais.lingolia.com/en/grammar/conjugator`.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
Data source attribution: [Lingolia Français](https://francais.lingolia.com/).
