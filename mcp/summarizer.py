from typing import Optional

def simple_summary(text: Optional[str], max_chars: int = 1000) -> str:
    """Return a very simple summary / excerpt of text.

    This is a placeholder; replace with a model-based summarizer later.
    """
    if not text:
        return ""
    excerpt = text.strip()[:max_chars]
    # Try not to cut mid-word
    if len(excerpt) < len(text) and " " in excerpt:
        excerpt = excerpt.rsplit(" ", 1)[0]
    return excerpt
