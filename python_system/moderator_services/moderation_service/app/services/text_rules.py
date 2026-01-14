"""
Rule-based text filtering for fast pre-screening
Complements ML models with explicit pattern matching
"""
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class RuleMatch:
    """Match result for a rule"""
    rule_name: str
    matched_text: str
    category: str
    severity: str  # low, medium, high, critical
    position: int
    keyword: str = ""  # The actual keyword that matched (for context analysis)


class TextRulesEngine:
    """
    Fast rule-based text filtering.

    Used for:
    - Pre-screening before ML models
    - Explicit keyword blocking
    - Pattern-based detection
    - Language-specific rules
    """

    # Critical keywords (auto-block)
    CRITICAL_KEYWORDS = {
        'violence': [
            'kill myself', 'suicide', 'self harm', 'cut myself',
            'end my life', 'hanging myself', 'overdose'
        ],
        'csam': [
            'child porn', 'cp', 'preteen', 'underage sex',
            'lolita', 'pedo', 'pedophile'
        ],
        'terrorism': [
            'bomb threat', 'terrorist attack', 'jihad recruitment',
            'isis', 'al qaeda', 'suicide bomber'
        ],
        'theft': [
            'stolen', 'stolen goods', 'hot goods', 'jacked',
            'off the truck', 'no receipt', 'no paperwork',
            'stolen iphone', 'stolen macbook', 'stolen laptop',
            'stolen phone', 'black market'
        ],
        'drugs_hard': [
            'buy heroin', 'sell cocaine', 'meth for sale',
            'fentanyl dealer', 'cartel',
            # Specific drug names (always block)
            'cocaine', 'heroin', 'methamphetamine', 'fentanyl',
            'crystal meth', 'crack cocaine', 'ecstasy', 'mdma',
            'lsd', 'pcp', 'ketamine', 'molly', 'speed',
            # Prescription abuse (standalone names)
            'oxycodone', 'xanax', 'adderall', 'vicodin', 'percocet',
            'oxy', 'oxy for sale', 'xanax for sale', 'pills without prescription',
            'prescription pills for sale', 'medication without prescription'
        ]
    }

    # High severity keywords (review)
    HIGH_KEYWORDS = {
        'weapons': [
            'weapon', 'weapons', 'gun', 'guns', 'rifle', 'pistol',
            'gun for sale', 'ak-47', 'ar-15', 'pistol sale',
            'ammunition', 'firearm', 'weapon dealer', 'knife for sale',
            'combat knife', 'switchblade', 'tactical knife',
            'hunting knife', 'military knife', 'tactical gear'
        ],
        'violence': [
            'beat up', 'assault', 'torture', 'murder for hire',
            'hitman', 'revenge attack'
        ],
        'hate': [
            'kill all', 'exterminate', 'genocide', 'racial slur',
            'hate crime', 'supremacy'
        ],
        'illegal': [
            'stolen goods', 'fake id', 'counterfeit', 'money laundering',
            'tax evasion', 'illegal immigrant', 'stolen', 'theft', 'hot goods',
            'jacked', 'no receipt', 'no paperwork', 'off the truck',
            'black market', 'under the table'
        ]
    }

    # Medium severity (flag)
    MEDIUM_KEYWORDS = {
        'drugs_soft': [
            'weed for sale', 'marijuana', 'cannabis dealer',
            'prescription pills'
        ],
        'adult': [
            'escort service', 'sex worker', 'massage parlor',
            'happy ending', 'no condom', 'sexual massage',
            'sensual massage', 'full service escort', 'call girl',
            'sexual services', 'sexual release', 'erotic massage',
            'adult services', 'prostitution'
        ],
        'gambling': [
            'sports betting', 'online casino', 'poker room',
            'guaranteed wins'
        ],
        'scam': [
            'miracle formula', 'guaranteed results', 'secret formula',
            'make money fast', 'get rich quick', 'work from home',
            'no effort needed', 'instant cash', 'earn $$$',
            'free money', 'risk free', 'guaranteed profit'
        ]
    }

    # Suspicious patterns
    PATTERNS = {
        'phone_spam': re.compile(r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}.*(?:call|text|whatsapp)', re.IGNORECASE),
        'url_spam': re.compile(r'https?://[^\s]+.*(?:click|visit|sign up|register)', re.IGNORECASE),
        'caps_spam': re.compile(r'\b[A-Z]{5,}\b'),  # All caps words
        'repeated_chars': re.compile(r'(.)\1{4,}'),  # aaaaa
        'excessive_punctuation': re.compile(r'[!?]{3,}'),  # !!!
        'money_pattern': re.compile(r'\$\d+(?:,\d{3})*(?:\.\d{2})?.*(?:guaranteed|easy|fast|quick)', re.IGNORECASE),
        'urgency': re.compile(r'\b(?:urgent|hurry|limited time|act now|expires|today only)\b', re.IGNORECASE)
    }

    # Obfuscation patterns
    OBFUSCATIONS = {
        r'[^\w\s]': '',  # Remove special chars
        r'(\w)\1+': r'\1',  # Deduplicate letters (heeeey → hey)
        r'\s+': ' '  # Normalize whitespace
    }

    def __init__(self):
        self.match_cache = {}

    def check(self, text: str) -> Dict[str, any]:
        """
        Run all rule checks on text.

        Args:
            text: Input text

        Returns:
            Dict with:
                - has_violations: bool
                - severity: str (critical/high/medium/low)
                - matches: List[RuleMatch]
                - flags: List[str]
                - should_block: bool
        """
        if not text or not text.strip():
            return self._empty_result()

        # Check cache
        text_hash = hash(text)
        if text_hash in self.match_cache:
            return self.match_cache[text_hash]

        matches = []
        flags = set()

        text_lower = text.lower()
        text_normalized = self._normalize_text(text)

        # 1. Critical keywords (auto-block)
        for category, keywords in self.CRITICAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matches.append(RuleMatch(
                        rule_name=f"critical_{category}",
                        matched_text=keyword,
                        category=category,
                        severity="critical",
                        position=text_lower.find(keyword),
                        keyword=keyword  # Add for context analysis
                    ))
                    flags.add(category)

        # 2. High severity keywords
        for category, keywords in self.HIGH_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matches.append(RuleMatch(
                        rule_name=f"high_{category}",
                        matched_text=keyword,
                        category=category,
                        severity="high",
                        position=text_lower.find(keyword),
                        keyword=keyword  # Add for context analysis
                    ))
                    flags.add(category)

        # 3. Medium severity keywords
        for category, keywords in self.MEDIUM_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matches.append(RuleMatch(
                        rule_name=f"medium_{category}",
                        matched_text=keyword,
                        category=category,
                        severity="medium",
                        position=text_lower.find(keyword),
                        keyword=keyword  # Add for context analysis
                    ))
                    flags.add(category)

        # 4. Pattern matching
        for pattern_name, pattern in self.PATTERNS.items():
            match = pattern.search(text)
            if match:
                matches.append(RuleMatch(
                    rule_name=f"pattern_{pattern_name}",
                    matched_text=match.group(0)[:50],
                    category="spam" if "spam" in pattern_name else "suspicious",
                    severity="medium",
                    position=match.start()
                ))
                flags.add(pattern_name)

        # 5. Check normalized text for obfuscation
        if text_normalized != text_lower:
            obfuscated_matches = self._check_obfuscated(text_normalized)
            matches.extend(obfuscated_matches)

        # Determine overall severity
        severity = self._determine_severity(matches)
        should_block = severity == "critical"

        result = {
            'has_violations': len(matches) > 0,
            'severity': severity,
            'matches': matches,
            'flags': list(flags),
            'should_block': should_block,
            'match_count': len(matches),
            'categories_flagged': list(set(m.category for m in matches))
        }

        # Cache result
        self.match_cache[text_hash] = result

        return result

    def _normalize_text(self, text: str) -> str:
        """Normalize text to catch obfuscated content"""
        normalized = text.lower()
        for pattern, replacement in self.OBFUSCATIONS.items():
            normalized = re.sub(pattern, replacement, normalized)
        return normalized.strip()

    def _check_obfuscated(self, normalized_text: str) -> List[RuleMatch]:
        """Check normalized text for obfuscated keywords"""
        matches = []

        # Check critical keywords in normalized form
        for category, keywords in self.CRITICAL_KEYWORDS.items():
            for keyword in keywords:
                keyword_normalized = self._normalize_text(keyword)
                if keyword_normalized in normalized_text:
                    matches.append(RuleMatch(
                        rule_name=f"obfuscated_{category}",
                        matched_text=keyword,
                        category=category,
                        severity="critical",
                        position=normalized_text.find(keyword_normalized)
                    ))

        return matches

    def _determine_severity(self, matches: List[RuleMatch]) -> str:
        """Determine overall severity from matches"""
        if not matches:
            return "low"

        severities = [m.severity for m in matches]

        if "critical" in severities:
            return "critical"
        elif "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"

    def _empty_result(self) -> Dict:
        """Return empty result for no violations"""
        return {
            'has_violations': False,
            'severity': 'low',
            'matches': [],
            'flags': [],
            'should_block': False,
            'match_count': 0,
            'categories_flagged': []
        }

    def add_custom_rule(self, category: str, keywords: List[str], severity: str = "medium"):
        """
        Add custom rules dynamically.

        Args:
            category: Category name
            keywords: List of keywords to match
            severity: critical/high/medium/low
        """
        if severity == "critical":
            if category not in self.CRITICAL_KEYWORDS:
                self.CRITICAL_KEYWORDS[category] = []
            self.CRITICAL_KEYWORDS[category].extend(keywords)
        elif severity == "high":
            if category not in self.HIGH_KEYWORDS:
                self.HIGH_KEYWORDS[category] = []
            self.HIGH_KEYWORDS[category].extend(keywords)
        else:
            if category not in self.MEDIUM_KEYWORDS:
                self.MEDIUM_KEYWORDS[category] = []
            self.MEDIUM_KEYWORDS[category].extend(keywords)

        # Clear cache when rules change
        self.match_cache.clear()

