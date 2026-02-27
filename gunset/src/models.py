"""
Data models and deck logic for Gunset API
"""
import random
import uuid
from datetime import datetime, timezone
from typing import Optional

SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


def create_deck() -> list[dict]:
    """Create a full deck of 54 cards (52 standard + 2 Jokers)."""
    deck = [{"rank": rank, "suit": suit} for suit in SUITS for rank in RANKS]
    deck.append({"rank": "JOKER", "suit": "Red"})
    deck.append({"rank": "JOKER", "suit": "Black"})
    return deck


def get_challenge(rank: str) -> str:
    """Get the shooting challenge description for a card rank."""
    if rank == 'JOKER':
        return "5 shots at 20 yards, 20 seconds par time"
    elif rank == 'A':
        return "5 shots at 11 yards, 11 seconds par time"
    elif rank in ['J', 'Q', 'K']:
        return "5 shots at 15 yards, 15 seconds par time"
    else:
        return f"5 shots at {rank} yards, {rank} seconds par time"


def get_current_week() -> tuple[int, int]:
    """Return (year, week_number) for the current ISO week."""
    now = datetime.now(timezone.utc)
    year, week, _ = now.isocalendar()
    return year, week


def create_new_deck_for_user(email: str) -> dict:
    """Create a new shuffled deck for a user."""
    deck_id = str(uuid.uuid4())
    cards = create_deck()
    random.shuffle(cards)

    return {
        "pk": f"DECK#{deck_id}",
        "sk": f"USER#{email}",
        "deck_id": deck_id,
        "email": email,
        "shuffled_cards": cards,
        "cards_drawn": 0,
        "draw_history": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }


def card_with_challenge(card: dict) -> dict:
    """Add challenge description to a card."""
    return {
        **card,
        "challenge": get_challenge(card["rank"]),
    }
