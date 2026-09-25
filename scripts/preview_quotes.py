"""Preview every quote in quotes.txt, rendered by GitHub's markdown renderer.

Run it from anywhere: python3 scripts/preview_quotes.py
It starts a small page on http://localhost:8765 (only reachable from this computer) with two buttons:
- Refresh preview: re-reads quotes.txt and renders it again
- Reroll live quote: runs the GitHub Action with reroll on, so your profile shows a different quote
Needs the gh CLI (logged in). Press Ctrl+C to stop it.
"""

import html
import subprocess
import sys
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PORT = 8765


def render(quote: str) -> str:
    # Same formatting the daily workflow uses.
    markdown = f"---\n\n{quote.replace(chr(92) + 'n', '<br>' + chr(10))}\n\n---"
    return subprocess.run(
        ["gh", "api", "markdown", "-f", "mode=gfm", "-f", f"text={markdown}"],
        capture_output=True, text=True, check=True,
    ).stdout


def build_page() -> str:
    quotes = [line.strip() for line in (REPO / "quotes.txt").read_text().splitlines() if line.strip()]
    with ThreadPoolExecutor(8) as pool:
        rendered = list(pool.map(render, quotes))
    cards = "".join(
        f'<section><h4>Quote {number}</h4><div class="markdown-body">{body}</div>'
        f"<details><summary>Raw line</summary><code>{html.escape(quote)}</code></details></section>"
        for number, (quote, body) in enumerate(zip(quotes, rendered), 1)
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Quote preview</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5/github-markdown-light.min.css">
<style>
  body {{ max-width: 830px; margin: 24px auto; padding: 0 16px; font-family: -apple-system, sans-serif; background: #fff; }}
  section {{ border: 1px solid #d0d7de; border-radius: 6px; padding: 8px 24px 16px; margin-bottom: 20px; }}
  h4 {{ color: #656d76; margin: 8px 0; }}
  code {{ word-break: break-all; font-size: 12px; }}
  summary {{ color: #656d76; font-size: 12px; cursor: pointer; }}
  .bar {{ position: sticky; top: 0; background: #fff; padding: 12px 0; display: flex; gap: 8px; align-items: center; border-bottom: 1px solid #d0d7de; margin-bottom: 20px; }}
  button {{ font: inherit; padding: 6px 14px; border-radius: 6px; border: 1px solid #d0d7de; background: #f6f8fa; cursor: pointer; }}
  button:disabled {{ opacity: .6; cursor: wait; }}
  #status {{ color: #656d76; font-size: 14px; }}
</style></head>
<body>
<h2>Uninspirational quote of the day: all {len(quotes)} quotes</h2>
<div class="bar">
  <button id="refresh">Refresh preview</button>
  <button id="reroll">Reroll live quote</button>
  <span id="status"></span>
</div>
{cards}
<script>
  const status = document.getElementById("status");
  document.getElementById("refresh").onclick = (e) => {{
    e.target.disabled = true;
    status.textContent = "Rendering quotes.txt...";
    location.reload();
  }};
  document.getElementById("reroll").onclick = async (e) => {{
    if (!confirm("Show a different random quote on your GitHub profile until midnight?")) return;
    e.target.disabled = true;
    status.textContent = "Starting the GitHub Action...";
    const response = await fetch("/reroll", {{ method: "POST", headers: {{ "X-Reroll": "1" }} }});
    status.textContent = await response.text();
    e.target.disabled = false;
  }};
</script>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        try:
            self.reply(200, "text/html", build_page())
        except (OSError, subprocess.CalledProcessError) as err:
            self.reply(500, "text/plain", f"Couldn't render the preview: {err}")

    def do_POST(self):
        # Other websites can't send this custom header to localhost, so only this page can reroll.
        if self.path != "/reroll" or self.headers.get("X-Reroll") != "1":
            self.send_error(404)
            return
        result = subprocess.run(
            ["gh", "workflow", "run", "quote.yml", "-f", "reroll=true"],
            cwd=REPO, capture_output=True, text=True,
        )
        if result.returncode == 0:
            self.reply(200, "text/plain", "Reroll started. Your profile updates in about a minute.")
        else:
            self.reply(500, "text/plain", f"Reroll failed: {result.stderr.strip()}")

    def reply(self, code: int, content_type: str, body: str):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"Quote preview running at {url} (Ctrl+C to stop)")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
