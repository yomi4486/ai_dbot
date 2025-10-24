import unittest

from mcp.summarizer import simple_summary


class TestSummarizer(unittest.TestCase):
    def test_simple_summary_short(self):
        text = "This is a short piece of text."
        out = simple_summary(text, max_chars=100)
        self.assertTrue(out.startswith("This is a short"))

    def test_simple_summary_truncate(self):
        text = "word " * 500
        out = simple_summary(text, max_chars=50)
        self.assertLessEqual(len(out), 50)


if __name__ == "__main__":
    unittest.main()
