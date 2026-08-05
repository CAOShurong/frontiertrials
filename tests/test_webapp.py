from __future__ import annotations

import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from frontiertrials import cli
from frontiertrials.webapp import CONTENT_SECURITY_POLICY, asset_text, make_server


class WebAppTests(unittest.TestCase):
    def test_packaged_assets_describe_personal_mode(self) -> None:
        html = asset_text("index.html")
        css = asset_text("styles.css")
        javascript = asset_text("app.js")
        self.assertIn("Which AI subscription earns a place", html)
        self.assertIn("Your text stays in this browser", html)
        self.assertIn("connect-src 'none'", html)
        self.assertIn("frontiertrials.personal.v1", javascript)
        self.assertIn("No product is favored", javascript)
        self.assertIn("characters", javascript)
        self.assertIn("--paper:", css)
        self.assertNotIn("<script>", html)

    def test_server_has_closed_network_policy_and_assets(self) -> None:
        server = make_server(port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with urllib.request.urlopen(f"{base}/", timeout=3) as response:
                body = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertEqual(
                    response.headers["Content-Security-Policy"], CONTENT_SECURITY_POLICY
                )
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertIn("FrontierTrials Personal Lab", body)
            with urllib.request.urlopen(f"{base}/app.js", timeout=3) as response:
                self.assertIn("javascript", response.headers["Content-Type"])
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(f"{base}/missing", timeout=3)
            self.assertEqual(raised.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_server_rejects_non_loopback_bindings(self) -> None:
        with self.assertRaisesRegex(ValueError, "loopback"):
            make_server("0.0.0.0", 8080)
        with self.assertRaisesRegex(ValueError, "port"):
            make_server(port=70000)

    def test_open_command_does_not_require_a_trial(self) -> None:
        args = cli._parser().parse_args(["open", "--port", "8765", "--no-browser"])
        with patch("frontiertrials.cli.serve_app") as serve:
            self.assertEqual(cli.run(args), 0)
        serve.assert_called_once_with(host="127.0.0.1", port=8765, open_browser=False)


if __name__ == "__main__":
    unittest.main()
