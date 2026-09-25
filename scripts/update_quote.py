"""Swap today's uninspirational quote into README.md.

Quotes come from the QUOTES environment variable (one per line), which the
workflow fills from a repository secret so the full list stays hidden.
"""

import datetime
import os
import random
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

README = Path("README.md")
START = "<!-- QUOTE:START -->"
END = "<!-- QUOTE:END -->"

quotes = [line.strip() for line in os.environ.get("QUOTES", "").splitlines() if line.strip()]
if not quotes:
    sys.exit("QUOTES is empty, add the QUOTES repository secret")

# Days since a fixed start, in Pacific time, so the quote flips at midnight PT.
today = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date()
day = (today - datetime.date(2026, 1, 1)).days

# Go through every quote once (in a shuffled order) before any repeats.
order = list(range(len(quotes)))
random.Random(day // len(quotes)).shuffle(order)
quote = quotes[order[day % len(quotes)]]

# A manual "reroll" run swaps in a random different quote until the next midnight.
if os.environ.get("REROLL") == "true":
    shown = re.search(re.escape(START) + r"\s*---\s*(.*?)\s*---\s*" + re.escape(END), README.read_text(), re.S)
    shown = shown.group(1).replace("<br>\n", "\\n") if shown else None
    quote = random.choice([q for q in quotes if q != shown] or quotes)
# Each quote is one line in the secret, so a literal \n marks a line break. It becomes a real
# newline too, so markdown that has to start a line (like > or -) works after it.
quote = quote.replace("\\n", "<br>\n")

# Blank lines around the quote matter: text directly above --- turns into a heading.
block = f"{START}\n\n---\n\n{quote}\n\n---\n\n{END}"
text = README.read_text()
new_text, count = re.subn(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
if count == 0:
    sys.exit(f"Couldn't find {START} / {END} markers in README.md")
README.write_text(new_text)
