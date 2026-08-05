"""Serve the zero-config personal comparison lab on localhost."""

from __future__ import annotations

import contextlib
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from typing import Final

ASSET_TYPES: Final = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}

CONTENT_SECURITY_POLICY: Final = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "connect-src 'none'; "
    "object-src 'none'; "
    "base-uri 'none'; "
    "frame-ancestors 'none'; "
    "form-action 'none'"
)


def asset_text(name: str) -> str:
    """Return one packaged web-app asset as UTF-8 text."""
    return files("frontiertrials").joinpath("web", name).read_text(encoding="utf-8")


class PersonalLabHandler(BaseHTTPRequestHandler):
    """Minimal asset-only handler with an intentionally closed network policy."""

    server_version = "FrontierTrialsPersonalLab/0.3"

    def do_GET(self) -> None:  # noqa: N802
        asset = ASSET_TYPES.get(self.path.split("?", 1)[0])
        if asset is None:
            self.send_error(HTTPStatus.NOT_FOUND, "Asset not found")
            return
        name, content_type = asset
        payload = asset_text(name).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        """Keep normal local use quiet."""


def make_server(host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    """Create a local personal-lab server without starting its loop."""
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("the personal lab only binds to a loopback address")
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    return ThreadingHTTPServer((host, port), PersonalLabHandler)


def serve_app(
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    open_browser: bool = True,
) -> None:
    """Serve the personal lab until interrupted."""
    server = make_server(host, port)
    display_host = "127.0.0.1" if host == "localhost" else host
    url = f"http://{display_host}:{server.server_port}/"
    print("FrontierTrials Personal Lab")
    print(f"  {url}")
    print("  Data stays in this browser. Press Ctrl+C to stop.")
    if open_browser:
        threading.Timer(0.15, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\nFrontierTrials Personal Lab stopped.")
    finally:
        with contextlib.suppress(OSError):
            server.server_close()
