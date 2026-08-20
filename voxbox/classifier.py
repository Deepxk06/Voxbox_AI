"""Lightweight question classifier.

Categories: GENERAL, CODING, CURRENT_INFORMATION, MATH, CREATIVE,
LONG_CONTEXT, SYSTEM_HELP.

Uses keyword heuristics only (no LLM call) to avoid burning tokens.
"""
import re

CATEGORY_GENERAL = "GENERAL"
CATEGORY_CODING = "CODING"
CATEGORY_CURRENT = "CURRENT_INFORMATION"
CATEGORY_MATH = "MATH"
CATEGORY_CREATIVE = "CREATIVE"
CATEGORY_LONG_CONTEXT = "LONG_CONTEXT"
CATEGORY_SYSTEM_HELP = "SYSTEM_HELP"

_CURRENT_PATTERNS = [
    r"\bcurrent\b", r"\blatest\b", r"\btoday'?s\b", r"\bthis week\b", r"\bthis month\b",
    r"\bbreaking\b", r"\brecent(ly)?\b", r"\bnew (version|release|update)\b",
    r"\bnow\b", r"\bright now\b", r"\bwho is the (current|new)\b",
    r"\bwho (is|was) the (president|pm|prime minister|ceo|cm|chief minister)\b",
    r"\bwhat is the (current|latest)\b", r"\bprice of\b", r"\bweather\b",
    r"\bnews\b", r"\belection\b", r"\bscore\b", r"\bresult of\b", r"\bstock\b",
    r"\beconomy\b", r"\binflation\b", r"\bgdp\b", r"\bcrypto\b", r"\bbitcoin\b",
    r"\biphone \d+\b", r"\bgemini\b.*\bversion\b", r"\bversion of python\b",
]

_CODING_PATTERNS = [
    r"\bcode\b", r"\bbug\b", r"\bdebug\b", r"\berror\b", r"\bexception\b",
    r"\bpython\b", r"\bjavascript\b", r"\btypescript\b", r"\bjava\b", r"\bc\+\+\b",
    r"\bgo(lang)?\b", r"\brust\b", r"\bsql\b", r"\bhtml\b", r"\bcss\b", r"\bbash\b",
    r"\bgit\b", r"\bdocker\b", r"\bregex\b", r"\bfunction\b", r"\bclass\b",
    r"\bapi\b", r"\bendpoint\b", r"\brequest\b", r"\bjson\b", r"\bflask\b",
    r"\bdjango\b", r"\breact\b", r"\bvue\b", r"\bangular\b", r"\bnpm\b", r"\bpip\b",
    r"\bcompile\b", r"\bdeploy\b", r"\btest(s|ing)?\b", r"\brefactor\b", r"\boptimize\b",
    r"\bsyntax\b", r"\bscript\b", r"\balgorithm\b", r"\bdata structure\b", r"\bschema\b",
    r"\bquery\b", r"\bstack trace\b", r"\bfix\b", r"\bexception\b", r"\btraceback\b",
]

_MATH_PATTERNS = [
    r"\bsolve\b", r"\bcalculate\b", r"\bequation\b", r"\bderivative\b", r"\bintegral\b",
    r"\bmath\b", r"\balgebra\b", r"\bcalculus\b", r"\bprobability\b", r"\bstatistics\b",
    r"\bmatrix\b", r"\bwhat is \d+\s*[+\-*/%^]", r"\bcompute\b",
]

_SYSTEM_PATTERNS = [
    r"\bwho are you\b", r"\bwhat (can|do) you do\b", r"\bhow (do|does) you work\b",
    r"\bhelp\b", r"\bcommands\b", r"\bsystem prompt\b", r"\binstructions\b",
]

_CODE_KEYWORDS = [
    "def ", "function ", "class ", "import ", "from ", "const ", "let ", "var ",
    "=>", "```", "print(", "return ", "self.", "async ", "await ", "SELECT ",
]


def classify(text: str) -> str:
    """Classify a user question. Returns one of the CATEGORY_* values."""
    if not text:
        return CATEGORY_GENERAL
    low = text.lower()
    if len(text) > 6000:
        return CATEGORY_LONG_CONTEXT
    if re.search(r"|".join(_SYSTEM_PATTERNS), low):
        return CATEGORY_SYSTEM_HELP
    if re.search(r"|".join(_CURRENT_PATTERNS), low):
        return CATEGORY_CURRENT
    if re.search(r"|".join(_MATH_PATTERNS), low):
        return CATEGORY_MATH
    if any(k in low for k in _CODE_KEYWORDS) or re.search(r"|".join(_CODING_PATTERNS), low):
        return CATEGORY_CODING
    if re.search(r"\b(write|compose|create|invent|story|poem|poetry|script)\b", low):
        return CATEGORY_CREATIVE
    return CATEGORY_GENERAL


def needs_web_search(category: str, text: str) -> bool:
    """Current-information questions trigger search; everything else does not."""
    if category == CATEGORY_CURRENT:
        return True
    return False