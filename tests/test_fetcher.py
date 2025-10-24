import unittest
from unittest.mock import patch, Mock

from mcp.fetcher import fetch_text_from_url


class TestFetcher(unittest.TestCase):
    @patch("mcp.fetcher.requests.get")
    def test_fetch_article(self, mock_get):
        html = "<html><body><article><p>First.</p><p>Second.</p></article></body></html>"
        mock_resp = Mock()
        mock_resp.text = html
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        out = fetch_text_from_url("https://example.com")
        self.assertIn("First.", out["text"])

    @patch("mcp.fetcher.requests.get")
    def test_fetch_paragraphs(self, mock_get):
        html = "<html><body><p>Para1</p><p>Para2</p></body></html>"
        mock_resp = Mock()
        mock_resp.text = html
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        out = fetch_text_from_url("https://example.com")
        self.assertIn("Para1", out["text"])


if __name__ == "__main__":
    unittest.main()
