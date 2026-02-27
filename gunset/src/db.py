"""
DynamoDB operations for Gunset API
"""
import os
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone, timedelta
from typing import Optional
import secrets

TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "gunset")

_dynamodb = None


def get_table():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb.Table(TABLE_NAME)


# --- User Operations ---

def get_user(email: str) -> Optional[dict]:
    """Get user by email."""
    table = get_table()
    response = table.get_item(Key={"pk": f"USER#{email}", "sk": "PROFILE"})
    return response.get("Item")


def create_user(email: str) -> dict:
    """Create a new user."""
    table = get_table()
    user = {
        "pk": f"USER#{email}",
        "sk": "PROFILE",
        "email": email,
        "current_deck_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    table.put_item(Item=user)
    return user


def get_or_create_user(email: str) -> dict:
    """Get existing user or create new one."""
    user = get_user(email)
    if not user:
        user = create_user(email)
    return user


def update_user_deck(email: str, deck_id: str):
    """Update user's current deck ID."""
    table = get_table()
    table.update_item(
        Key={"pk": f"USER#{email}", "sk": "PROFILE"},
        UpdateExpression="SET current_deck_id = :deck_id",
        ExpressionAttributeValues={":deck_id": deck_id},
    )


# --- Session Operations (Magic Links) ---

def create_session(email: str, ttl_minutes: int = 15) -> str:
    """Create a magic link session token."""
    table = get_table()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)

    session = {
        "pk": f"SESSION#{token}",
        "sk": "MAGIC_LINK",
        "email": email,
        "verified": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": int(expires_at.timestamp()),  # TTL attribute
    }
    table.put_item(Item=session)
    return token


def verify_session(token: str) -> Optional[str]:
    """
    Verify a magic link token and return the email if valid.
    Returns None if invalid or expired.
    """
    table = get_table()
    response = table.get_item(Key={"pk": f"SESSION#{token}", "sk": "MAGIC_LINK"})
    session = response.get("Item")

    if not session:
        return None

    # Check expiration
    if session["expires_at"] < int(datetime.now(timezone.utc).timestamp()):
        return None

    # Delete the session so the magic link can't be reused
    table.delete_item(Key={"pk": f"SESSION#{token}", "sk": "MAGIC_LINK"})

    return session["email"]


def create_auth_token(email: str, ttl_days: int = 30) -> str:
    """Create a long-lived auth token after magic link verification."""
    table = get_table()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_days)

    auth = {
        "pk": f"AUTH#{token}",
        "sk": "TOKEN",
        "email": email,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": int(expires_at.timestamp()),
    }
    table.put_item(Item=auth)
    return token


def validate_auth_token(token: str) -> Optional[str]:
    """Validate auth token and return email if valid."""
    table = get_table()
    response = table.get_item(Key={"pk": f"AUTH#{token}", "sk": "TOKEN"})
    auth = response.get("Item")

    if not auth:
        return None

    if auth["expires_at"] < int(datetime.now(timezone.utc).timestamp()):
        return None

    return auth["email"]


# --- Deck Operations ---

def get_deck(deck_id: str, email: str) -> Optional[dict]:
    """Get a specific deck."""
    table = get_table()
    response = table.get_item(Key={"pk": f"DECK#{deck_id}", "sk": f"USER#{email}"})
    return response.get("Item")


def save_deck(deck: dict):
    """Save a deck to DynamoDB."""
    table = get_table()
    table.put_item(Item=deck)


def get_user_decks(email: str) -> list[dict]:
    """Get all decks for a user (for history)."""
    table = get_table()
    # Use a GSI to query by email
    response = table.query(
        IndexName="email-index",
        KeyConditionExpression=Key("email").eq(email),
        FilterExpression="begins_with(pk, :prefix)",
        ExpressionAttributeValues={":prefix": "DECK#"},
    )
    return sorted(response.get("Items", []), key=lambda x: x["created_at"], reverse=True)


def draw_card_from_deck(deck: dict, year: int, week: int) -> Optional[dict]:
    """
    Draw the next card from a deck for a given week.
    Returns the card if drawn, None if deck is complete.
    Updates the deck in place.
    """
    cards_drawn = int(deck["cards_drawn"])

    if cards_drawn >= 54:
        return None  # Deck complete

    # Get the next card
    card = deck["shuffled_cards"][cards_drawn]

    # Update deck state
    deck["cards_drawn"] = cards_drawn + 1
    deck["draw_history"].append({
        "card": card,
        "year": year,
        "week": week,
        "drawn_at": datetime.now(timezone.utc).isoformat(),
    })

    # Mark complete if this was the last card
    if deck["cards_drawn"] >= 54:
        deck["completed_at"] = datetime.now(timezone.utc).isoformat()

    return card


def get_card_for_week(deck: dict, year: int, week: int) -> Optional[dict]:
    """Check if a card was already drawn for this week."""
    for entry in deck["draw_history"]:
        if entry["year"] == year and entry["week"] == week:
            return entry["card"]
    return None
