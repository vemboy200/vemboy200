"""The format of the quote list, shared by the daily workflow and the preview page.

The list lives in quotes.md locally and in the QUOTES repository secret on GitHub.
Each quote is normal markdown, and a line with just % goes between quotes.
Line breaks are kept, like in a GitHub comment.
"""

import re

SEPARATOR = re.compile(r"^%[ \t]*$", re.M)
COMMENT_ONLY = re.compile(r"(\s*<!--.*?-->)+\s*", re.S)


def parse(text: str) -> list[str]:
    if not SEPARATOR.search(text):
        # The old format: one quote per line, with a literal \n for each line break.
        return [line.strip().replace("\\n", "\n") for line in text.splitlines() if line.strip()]
    chunks = (chunk.strip() for chunk in SEPARATOR.split(text))
    # A chunk that's only <!-- comments --> is a note in the file, not a quote.
    return [chunk for chunk in chunks if chunk and not COMMENT_ONLY.fullmatch(chunk)]


def render(quote: str) -> str:
    """Markdown for the README. A single line break would get merged into one line, so add <br>."""
    lines = quote.splitlines()
    in_code = False
    for i, line in enumerate(lines[:-1]):
        fence = line.lstrip().startswith("```")
        if fence:
            in_code = not in_code
        # Leave code blocks and tables alone, <br> would break them.
        if not (fence or in_code) and line.strip() and lines[i + 1].strip() and not line.lstrip().startswith("|"):
            lines[i] = line + "<br>"
    return "\n".join(lines)
