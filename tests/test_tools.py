"""
tests/test_tools.py

Pytest tests for all three FitFindr tools, covering the failure modes
documented in planning.md plus one success-path test per tool.

LLM-backed tools (suggest_outfit, create_fit_card) are tested with a mocked
Groq client so no real API calls are made and tests are deterministic.
"""

from unittest.mock import MagicMock, patch

import pytest

from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe


# ── Shared fixtures ───────────────────────────────────────────────────────────

SAMPLE_ITEM = {
    "id": "lst_001",
    "title": "Vintage Levi's 501 Jeans — Medium Wash",
    "category": "bottoms",
    "style_tags": ["vintage", "classic", "denim", "streetwear"],
    "size": "W30 L30",
    "condition": "good",
    "price": 38.00,
    "colors": ["blue", "indigo"],
    "brand": "Levi's",
    "platform": "depop",
}


def _mock_client(content="Mock LLM response."):
    """Return a MagicMock Groq client whose chat completion returns `content`."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = content
    mock = MagicMock()
    mock.chat.completions.create.return_value = mock_response
    return mock


# ── search_listings ───────────────────────────────────────────────────────────

class TestSearchListings:
    def test_no_results_returns_empty_list(self):
        # Failure mode: query that matches nothing
        result = search_listings("ballgown", size="XXS", max_price=5.0)
        assert result == []

    def test_no_results_does_not_raise(self):
        # Nonsense description should return a list, not raise
        result = search_listings("zzz_nonexistent_item_zzz")
        assert isinstance(result, list)

    def test_normal_match_returns_results(self):
        result = search_listings("vintage graphic tee")
        assert len(result) > 0
        assert "title" in result[0]

    def test_price_filter_respected(self):
        result = search_listings("vintage", max_price=25.0)
        assert result  # at least one match
        assert all(listing["price"] <= 25.0 for listing in result)

    def test_size_filter_respected(self):
        # "M" is a substring of sizes like "S/M" and "M/L" in the dataset
        result = search_listings("top", size="M")
        assert result  # at least one match
        assert all("m" in listing["size"].lower() for listing in result)


# ── suggest_outfit ────────────────────────────────────────────────────────────

class TestSuggestOutfit:
    def test_empty_wardrobe_returns_nonempty_string(self):
        # Failure mode: wardrobe has no items → fallback suggestion, not empty
        with patch("tools._get_groq_client", return_value=_mock_client("Great with slim jeans.")):
            result = suggest_outfit(SAMPLE_ITEM, get_empty_wardrobe())
        assert isinstance(result, str)
        assert result.strip()

    def test_empty_wardrobe_does_not_raise(self):
        with patch("tools._get_groq_client", return_value=_mock_client("Fallback styling tip.")):
            result = suggest_outfit(SAMPLE_ITEM, get_empty_wardrobe())
        assert result  # truthy — never crashes

    def test_missing_items_key_does_not_raise(self):
        # wardrobe={} has no 'items' key — must not raise KeyError
        with patch("tools._get_groq_client", return_value=_mock_client("Generic tip.")):
            result = suggest_outfit(SAMPLE_ITEM, {})
        assert isinstance(result, str)

    def test_example_wardrobe_returns_suggestion(self):
        with patch("tools._get_groq_client", return_value=_mock_client("Pair with white ribbed tank.")):
            result = suggest_outfit(SAMPLE_ITEM, get_example_wardrobe())
        assert result.strip()


# ── create_fit_card ───────────────────────────────────────────────────────────

class TestCreateFitCard:
    def test_empty_outfit_returns_error_string(self):
        # Failure mode: empty outfit → descriptive error, no exception
        result = create_fit_card("", SAMPLE_ITEM)
        assert "No outfit suggestion available" in result

    def test_whitespace_outfit_returns_error_string(self):
        result = create_fit_card("   ", SAMPLE_ITEM)
        assert "No outfit suggestion available" in result

    def test_empty_outfit_does_not_raise(self):
        result = create_fit_card("", SAMPLE_ITEM)
        assert isinstance(result, str)

    def test_normal_input_returns_caption(self):
        outfit = "Pair with baggy jeans and chunky sneakers for a 90s vibe."
        with patch("tools._get_groq_client", return_value=_mock_client("Found this thrifted tee on depop for $38.")):
            result = create_fit_card(outfit, SAMPLE_ITEM)
        assert isinstance(result, str)
        assert result.strip()
