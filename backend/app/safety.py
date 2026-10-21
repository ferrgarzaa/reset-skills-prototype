"""Safety checks that run in code, not in the prompt.

1. crisis_match(): runs on user text BEFORE any model call.
2. clean_reply(): runs on every model reply BEFORE it is shown or saved.

Limits (documented in docs/design.md): the keyword list misses indirect
wording and typos, and it cannot understand context. It errs on the side of
opening the crisis panel, because a false alarm only shows information.
"""
import re

# Phrases are matched on lowercase text with curly apostrophes normalized.
CRISIS_PATTERNS = [
    r"\bsuicid\w*",
    r"\bkill(ing)? my ?self\b",
    r"\bend(ing)? (my|it) (life|all)\b",
    r"\bend it all\b",
    r"\btake my (own )?life\b",
    r"\bwant(ed)? to die\b",
    r"\bwish i (was|were) dead\b",
    r"\bbetter off (dead|without me)\b",
    r"\bno reason to (live|go on|keep going)\b",
    r"\bdon'?t want to (live|be alive|be here anymore|wake up)\b",
    r"\bcan'?t go on\b",
    r"\bself[- ]?harm\w*",
    r"\bhurt(ing)? my ?self\b",
    r"\bcut(ting)? my ?self\b",
    r"\boverdos\w*",
    r"\bnot safe (right now|with myself)\b",
]
_CRISIS_RE = re.compile("|".join(CRISIS_PATTERNS))

CRISIS_MESSAGE = (
    "It sounds like things are really heavy right now. This app can't help in a crisis, "
    "but people can. The crisis options are open on your screen. You can call or text 988 "
    "any time, or call 911 if you're in danger. Your words are saved here, and you can come "
    "back whenever you want."
)


def normalize(text: str) -> str:
    return text.lower().replace("’", "'").replace("‘", "'")


def crisis_match(text: str) -> bool:
    return bool(_CRISIS_RE.search(normalize(text)))


# Words a reply must never contain. If found, the reply is replaced by a fixed line.
BLOCKED_ALWAYS = [
    r"\bdiagnos\w*",
    r"\bdisorder\b",
    r"\bborderline\b",
    r"\bbpd\b",
    r"\bmedication\b",
    r"\bprescri\w*",
    r"\bi'?m (a|your) therapist\b",
    r"\bi am (a|your) therapist\b",
    r"\bas your therapist\b",
    r"\bour therapy\b",
    r"\bmonitor\w*",
    r"\bi'?ll check (in|on you)\b",
    r"\bsomeone will (contact|reach out|check)\b",
    r"\bi'?ve been (watching|tracking)\b",
]
# Extra rules for the very short lines around an exercise.
BLOCKED_SHORT = [r"\byou should\b", r"\byou need to\b", r"\bgreat job\b", r"\bproud of you\b"]

_EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF]")


def clean_reply(text: str, max_words: int, short: bool = False) -> str | None:
    """Return a safe version of the reply, or None if it must be replaced."""
    if not text:
        return None
    t = text.strip()
    low = normalize(t)
    patterns = BLOCKED_ALWAYS + (BLOCKED_SHORT if short else [])
    if any(re.search(p, low) for p in patterns):
        return None
    t = _EMOJI_RE.sub("", t)
    t = t.replace("!", ".")
    t = re.sub(r"\.{2,}", ".", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    if len(t.split()) > max_words:
        return None
    return t
