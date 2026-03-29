#!/usr/bin/env python3
"""
News Credibility Checker — Lightweight HTTP Server
====================================================
Uses only Python stdlib + bs4 + lxml (no FastAPI/Flask needed).

POST /api/check  → JSON credibility analysis
GET  /           → frontend UI
GET  /health     → health check
"""

import json
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

from analyzer import NewsAnalyzer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("server")

analyzer = NewsAnalyzer()

# Load frontend HTML from main.py (the HTML_PAGE constant)
FRONTEND_HTML = ""
_main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend.html")
if os.path.exists(_main_path):
    with open(_main_path, encoding="utf-8") as f:
        FRONTEND_HTML = f.read()


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/health":
            self._json_response({"status": "ok", "service": "news-checker"})
        elif self.path == "/" or self.path.startswith("/?"):
            self._html_response(FRONTEND_HTML or "<h1>News Checker</h1><p>frontend.html not found</p>")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/check":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._json_response({"error": "invalid JSON"}, 400)
                return

            text = data.get("text", "")
            url = data.get("url", "")

            if not text and not url:
                self._json_response({"error": "please provide 'text' or 'url'"}, 400)
                return

            log.info(f"Analyzing: text={len(text)} chars, url={url[:60] if url else 'none'}")
            result = analyzer.analyze(text=text, url=url)
            self._json_response(result.to_dict())
        else:
            self.send_error(404)

    def _json_response(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html_response(self, html, code=200):
        body = html.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        log.info(format % args)


def main():
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    log.info(f"News Checker running on http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
