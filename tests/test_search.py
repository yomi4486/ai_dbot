import unittest
from unittest.mock import patch, Mock

from mcp.search import serpapi_search, SerpApiError


class TestSerpApiSearch(unittest.TestCase):
    @patch("mcp.search.requests.get")
    def test_serpapi_search_success(self, mock_get):
        fake_json = {
            "organic_results": [
                {"title": "T1", "link": "https://a.example", "snippet": "S1"},
                {"title": "T2", "link": "https://b.example", "snippet": "S2"},
            ]
        }
        mock_resp = Mock()
        mock_resp.json.return_value = fake_json
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        # Temporarily ensure SERPAPI_KEY exists by patching the module env var
        with patch("mcp.search.SERPAPI_KEY", "dummy_key"):
            results = serpapi_search("query", num=2)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["title"], "T1")

    def test_serpapi_no_key(self):
        with patch("mcp.search.SERPAPI_KEY", None):
            with self.assertRaises(SerpApiError):
                serpapi_search("q")


if __name__ == "__main__":
    unittest.main()
