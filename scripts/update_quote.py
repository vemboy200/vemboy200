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
# Each quote is one line in the secret, so a literal \n marks a line break.
quote = quote.replace("\\n", "<br>")

block = f"{START}\n> {quote}\n{END}"
text = README.read_text()
new_text, count = re.subn(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
if count == 0:
    sys.exit(f"Couldn't find {START} / {END} markers in README.md")
README.write_text(new_text)
