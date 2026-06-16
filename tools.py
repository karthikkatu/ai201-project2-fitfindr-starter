"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    if size is not None:
        size_lower = size.lower()
        listings = [l for l in listings if size_lower in l["size"].lower()]

    keywords = set(description.lower().split())

    def _score(listing: dict) -> int:
        tokens: set[str] = set()
        for field in (listing["title"], listing["description"], listing["category"]):
            tokens.update(field.lower().split())
        for tag in listing["style_tags"]:
            tokens.update(tag.lower().split())
        for color in listing["colors"]:
            tokens.update(color.lower().split())
        if listing["brand"]:
            tokens.update(listing["brand"].lower().split())
        return len(keywords & tokens)

    scored = [(s, l) for l in listings if (s := _score(l)) > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [l for _, l in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()
    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []

    if not wardrobe_items:
        prompt = (
            f"You are a fashion stylist. A user is considering buying this secondhand item:\n"
            f"- Name: {new_item.get('title', 'unknown item')}\n"
            f"- Category: {new_item.get('category', '')}\n"
            f"- Style tags: {', '.join(new_item.get('style_tags', []))}\n"
            f"- Colors: {', '.join(new_item.get('colors', []))}\n"
            f"- Condition: {new_item.get('condition', '')}\n\n"
            "The user hasn't shared their wardrobe yet. Give 1–2 short, specific styling suggestions: "
            "what types of pieces pair well with this item, what vibe it suits, and how to wear it. "
            "Be casual and direct, like a knowledgeable friend."
        )
    else:
        wardrobe_lines = "\n".join(
            f"- {item['name']} ({item['category']}, colors: {', '.join(item.get('colors', []))})"
            for item in wardrobe_items
        )
        prompt = (
            f"You are a fashion stylist. A user is considering buying this secondhand item:\n"
            f"- Name: {new_item.get('title', 'unknown item')}\n"
            f"- Category: {new_item.get('category', '')}\n"
            f"- Style tags: {', '.join(new_item.get('style_tags', []))}\n"
            f"- Colors: {', '.join(new_item.get('colors', []))}\n"
            f"- Condition: {new_item.get('condition', '')}\n\n"
            f"Their wardrobe includes:\n{wardrobe_lines}\n\n"
            "Suggest 1–2 complete outfits that combine this new item with specific pieces from their wardrobe. "
            "Name the wardrobe pieces by name. Be specific about layering, color matching, and the overall vibe. "
            "Keep it short, casual, and stylistically concrete."
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        title = new_item.get("title", "this item")
        return (
            f"Style tip for {title}: pair it with basics in complementary colors "
            f"and let the piece be the focal point of your outfit. ({exc})"
        )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or (isinstance(outfit, str) and not outfit.strip()):
        return "No outfit suggestion available — can't generate a fit card without styling details."

    outfit_text = outfit if isinstance(outfit, str) else str(outfit)

    client = _get_groq_client()
    title = new_item.get("title", "this thrifted find")
    price = new_item.get("price", "")
    platform = new_item.get("platform", "")
    colors = ", ".join(new_item.get("colors", []))
    tags = ", ".join(new_item.get("style_tags", []))

    prompt = (
        f"You are writing a casual social-media caption for a thrift-fashion post.\n\n"
        f"Thrifted item:\n"
        f"- Name: {title}\n"
        f"- Price: ${price}\n"
        f"- Platform: {platform}\n"
        f"- Colors: {colors}\n"
        f"- Vibe: {tags}\n\n"
        f"Outfit idea:\n{outfit_text}\n\n"
        "Write a 2–4 sentence Instagram or TikTok caption for this outfit. "
        "Mention the item name, price, and platform naturally (once each). "
        "Make it sound like a real person posting their OOTD — casual, specific, not generic. "
        "No hashtags, no emojis unless they feel natural."
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.2,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        return f"Couldn't generate a fit card right now: {exc}"
