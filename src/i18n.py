"""Screen texts in the selected language.

Each language is a JSON file, lang_<code>.json, mapping text keys to
uppercase screen text (MicroPython's str.upper() only handles ASCII, so
accented capitals are written directly). Only the active language is kept
in memory. The choice is saved in LANGUAGE_FILE and survives restarts.
"""

import json

from config import DEFAULT_LANGUAGE, LANGUAGES

LANGUAGE_FILE = "/language.cfg"
# Folder holding the lang_<code>.json files; the board keeps them next to
# main.py. Tests point this at src/.
TEXT_DIR = "/"

texts = {}
language = None


def load(code):
    """Make `code` the active language; raises OSError or ValueError."""
    global texts, language
    with open("%slang_%s.json" % (TEXT_DIR, code)) as text_file:
        texts = json.load(text_file)
    language = code


def start():
    """Load the saved language, falling back to the default."""
    code = DEFAULT_LANGUAGE
    try:
        with open(LANGUAGE_FILE) as language_file:
            saved = language_file.read().strip()
        if saved in LANGUAGES:
            code = saved
    except OSError:
        pass
    for candidate in (code, DEFAULT_LANGUAGE):
        try:
            load(candidate)
            return
        except (OSError, ValueError) as exc:
            print("Language %s unavailable:" % candidate, exc)
    print("No language file loaded; showing text keys.")


def t(key):
    """Return the active language's text for `key` (the key if missing)."""
    return texts.get(key, key)


def next_language():
    if language not in LANGUAGES:
        return LANGUAGES[0]
    return LANGUAGES[(LANGUAGES.index(language) + 1) % len(LANGUAGES)]


def save():
    with open(LANGUAGE_FILE, "w") as language_file:
        language_file.write(language + "\n")
