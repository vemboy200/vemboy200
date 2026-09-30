"""Put vemboy200's claude-rpc token leaderboard rank into README.md as a badge."""

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

README = Path("README.md")
HANDLE = "vemboy200"
LEADERBOARD = "https://claude-rpc-totals.claude-rpc.workers.dev/leaderboard?metric=tokens"

# Cloudflare blocks Python's default user agent, so say who's asking.
request = urllib.request.Request(LEADERBOARD, headers={"User-Agent": f"{HANDLE}-profile-readme"})
with urllib.request.urlopen(request, timeout=30) as response:
    board = json.load(response)["leaderboard"]

# The leaderboard only lists the top 50.
rank = next((f"#{entry['rank']}" for entry in board if entry["handle"] == HANDLE), f"not top {len(board)}")

# shields.io static badge: dashes and underscores need doubling, the rest is URL-escaped.
def shields(text: str) -> str:
    return urllib.parse.quote(text.replace("-", "--").replace("_", "__"))

badge = f"https://img.shields.io/badge/{shields('claude-rpc token rank')}-{shields(rank)}-d97757"
new_badge = f"[![claude-rpc token rank: {rank}]({badge})](https://claude-rpc.com/?ref=badge)"

# Find the existing rank badge wherever it is in the README and swap it for the new one.
pattern = r"\[!\[claude-rpc token rank: [^\]]*\]\(https://img\.shields\.io/badge/claude--rpc[^)]*\)\]\([^)]*\)"
text = README.read_text()
new_text, count = re.subn(pattern, lambda _: new_badge, text)
if count == 0:
    sys.exit("Couldn't find the claude-rpc token rank badge in README.md")
README.write_text(new_text)
print(f"Rank: {rank}")
