"""
Text Normalizer
===============

Step 2: text normalization, cleaning, and tokenization.
"""

import sys
import re
import unicodedata
from typing import List, Dict, Optional


class TextNormalizer:
    """Step 2: normalization + tokenization"""

    def __init__(self, enable_emoji=True, aggressive=False):
        self.enable_emoji = enable_emoji
        self.aggressive = aggressive

        self.spacy_nlp = None
        self._load_spacy()

        # Precompiled regex patterns for performance
        self._ws_re = re.compile(r"\s+")
        self._control_re = re.compile(r"[\u0000-\u001F\u007F]")
        self._zero_width_re = re.compile(r"[\u200B-\u200D\uFEFF]")
        self._punct_clean_re = re.compile(r"[^\w\s\.,!?\'\-]")


    def _load_spacy(self):
        """Load spaCy tokenizer if available"""
        try:
            import spacy
            try:
                self.spacy_nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger", "ner"])
            except OSError:
                import subprocess
                subprocess.run(
                    [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                    capture_output=True
                )
                self.spacy_nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger", "ner"])

            print("✓ spaCy tokenizer initialized")
        except Exception:
            print("⚠ spaCy unavailable - falling back to regex tokenization")


    def normalize(self, text: str) -> str:
        """Normalize + clean text safely"""
        if not text:
            return ""

        # Unicode canonical normalization
        text = unicodedata.normalize("NFKC", text)

        # Remove control chars + zero-width spaces
        text = self._control_re.sub("", text)
        text = self._zero_width_re.sub("", text)

        # Lowercase
        text = text.lower()

        # Emoji support (optional)
        if not self.enable_emoji:
            text = re.sub(r"[^\x00-\x7F]+", " ", text)

        # Collapse whitespace
        text = self._ws_re.sub(" ", text).strip()

        # Remove unwanted chars but keep basic punctuation
        cleaned = self._punct_clean_re.sub("", text)

        # Aggressive mode removes all punctuation
        if self.aggressive:
            cleaned = re.sub(r"[^\w\s]", "", cleaned)

        return cleaned


    def tokenize(self, text: str) -> List[str]:
        """Tokenize into surface tokens"""
        if self.spacy_nlp:
            doc = self.spacy_nlp(text)
            return [t.text for t in doc if t.text.strip()]
        return re.findall(r"\w+|[.,!?]", text)


    def extract_entities(self, text: str) -> List[Dict]:
        """
        Extract entities if spaCy supports NER model.
        Fails gracefully if no NER module exists.
        """
        if not self.spacy_nlp:
            return []

        try:
            doc = self.spacy_nlp(text)
            if not hasattr(doc, "ents"):
                return []
            return [
                {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                }
                for ent in doc.ents
            ]
        except Exception:
            return []
