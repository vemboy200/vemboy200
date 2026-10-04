"""Swap today's uninspirational quote into README.md.

Quotes come from the QUOTES environment variable (the contents of quotes.md,
see quote_format.py), which the workflow fills from a repository secret so the
full list stays hidden.

"We're making it less random to make it feel more random." A quote never
comes back until at least half the list (rounded up) has been shown since.
To remember what was shown, the README keeps a hidden comment with short
hashes of recent quotes. Hashes of quotes that were already public reveal
nothing about the ones that weren't.
"""

import datetime
import hashlib
import math
import os
import random
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from quote_format import parse, render

README = Path("README.md")
START = "<!-- QUOTE:START -->"
END = "<!-- QUOTE:END -->"
BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
HISTORY = re.compile(r"<!-- shown: (\S+)((?: [0-9a-f]{8})*) -->")
SHOWN_QUOTE = re.compile(r"---\s*(.*?)\s*---", re.S)


def short_hash(quote: str) -> str:
    return hashlib.sha256(quote.encode()).hexdigest()[:8]


quotes = parse(os.environ.get("QUOTES", ""))
if not quotes:
    sys.exit("QUOTES is empty, add the QUOTES repository secret")
by_hash = {short_hash(q): q for q in quotes}

text = README.read_text()
block = BLOCK.search(text)
if not block:
    sys.exit(f"Couldn't find {START} / {END} markers in README.md")

# Read the history of shown quotes, oldest first. Before the history existed, start it
# with whatever quote is on the README right now.
history_match = HISTORY.search(block.group())
if history_match:
    last_day, history = history_match.group(1), history_match.group(2).split()
else:
    shown = SHOWN_QUOTE.search(block.group())
    shown = shown.group(1).replace("<br>\n", "\n") if shown else ""
    last_day, history = "", [short_hash(shown)] if short_hash(shown) in by_hash else []
current = history[-1] if history else None

# Midnight Pacific decides what "today" is.
today = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
number = os.environ.get("QUOTE_NUMBER", "").strip()
reroll = os.environ.get("REROLL") == "true"

if number:
    # A manual run can pick a specific quote by its number in quotes.md (starting at 1).
    if not number.isdigit() or not 1 <= int(number) <= len(quotes):
        sys.exit(f"Quote number must be between 1 and {len(quotes)}, got {number!r}")
    quote = quotes[int(number) - 1]
elif reroll or last_day != today or current not in by_hash:
    # New day, a reroll, or today's quote was removed from the list: pick one that hasn't
    # been shown in the last ceil(count / 2) picks.
    recent = set(history[-math.ceil(len(quotes) / 2):])
    choices = [q for q in quotes if short_hash(q) not in recent] or [q for q in quotes if short_hash(q) != current]
    quote = random.choice(choices or quotes)
else:
    print("Today's quote is already up")
    sys.exit()

history = (history + [short_hash(quote)])[-len(quotes):]

# Blank lines around the quote matter: text directly above --- turns into a heading.
new_block = (
    f"{START}\n<!-- shown: {today} {' '.join(history)} -->\n\n---\n\n"
    f"{render(quote)}\n\n---\n\n{END}"
)
README.write_text(text[: block.start()] + new_block + text[block.end():])
