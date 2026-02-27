"""Tests for db.py - DynamoDB operations using mocked table."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

import db


@pytest.fixture
def mock_table():
    """Provide a mocked DynamoDB table and reset the global cache."""
    table = MagicMock()
    db._dynamodb = None
    with patch('db.get_table', return_value=table):
        yield table


class TestUserOperations:
    def test_get_user_returns_item(self, mock_table):
        mock_table.get_item.return_value = {
            "Item": {"pk": "USER#test@example.com", "sk": "PROFILE", "email": "test@example.com"}
        }
        user = db.get_user("test@example.com")
        assert user["email"] == "test@example.com"
        mock_table.get_item.assert_called_once_with(
            Key={"pk": "USER#test@example.com", "sk": "PROFILE"}
        )

    def test_get_user_returns_none_when_not_found(self, mock_table):
        mock_table.get_item.return_value = {}
        assert db.get_user("nobody@example.com") is None

    def test_create_user_puts_item(self, mock_table):
        user = db.create_user("new@example.com")
        assert user["pk"] == "USER#new@example.com"
        assert user["sk"] == "PROFILE"
        assert user["email"] == "new@example.com"
        assert user["current_deck_id"] is None
        mock_table.put_item.assert_called_once()

    def test_get_or_create_returns_existing(self, mock_table):
        existing = {"pk": "USER#test@example.com", "sk": "PROFILE", "email": "test@example.com"}
        mock_table.get_item.return_value = {"Item": existing}
        result = db.get_or_create_user("test@example.com")
        assert result == existing
        mock_table.put_item.assert_not_called()

    def test_get_or_create_creates_new(self, mock_table):
        mock_table.get_item.return_value = {}
        result = db.get_or_create_user("new@example.com")
        assert result["email"] == "new@example.com"
        mock_table.put_item.assert_called_once()

    def test_update_user_deck(self, mock_table):
        db.update_user_deck("test@example.com", "deck-123")
        mock_table.update_item.assert_called_once_with(
            Key={"pk": "USER#test@example.com", "sk": "PROFILE"},
            UpdateExpression="SET current_deck_id = :deck_id",
            ExpressionAttributeValues={":deck_id": "deck-123"},
        )


class TestSessionOperations:
    def test_create_session_returns_token(self, mock_table):
        token = db.create_session("test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0
        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args[1]["Item"]
        assert item["pk"].startswith("SESSION#")
        assert item["sk"] == "MAGIC_LINK"
        assert item["email"] == "test@example.com"

    def test_verify_session_returns_email_for_valid_token(self, mock_table):
        future_ts = int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp())
        mock_table.get_item.return_value = {
            "Item": {
                "pk": "SESSION#abc123",
                "sk": "MAGIC_LINK",
                "email": "test@example.com",
                "expires_at": future_ts,
            }
        }
        result = db.verify_session("abc123")
        assert result == "test@example.com"

    def test_verify_session_deletes_token_after_use(self, mock_table):
        future_ts = int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp())
        mock_table.get_item.return_value = {
            "Item": {
                "pk": "SESSION#abc123",
                "sk": "MAGIC_LINK",
                "email": "test@example.com",
                "expires_at": future_ts,
            }
        }
        db.verify_session("abc123")
        mock_table.delete_item.assert_called_once_with(
            Key={"pk": "SESSION#abc123", "sk": "MAGIC_LINK"}
        )

    def test_verify_session_returns_none_for_missing_token(self, mock_table):
        mock_table.get_item.return_value = {}
        assert db.verify_session("nonexistent") is None

    def test_verify_session_returns_none_for_expired_token(self, mock_table):
        past_ts = int((datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp())
        mock_table.get_item.return_value = {
            "Item": {
                "pk": "SESSION#expired",
                "sk": "MAGIC_LINK",
                "email": "test@example.com",
                "expires_at": past_ts,
            }
        }
        result = db.verify_session("expired")
        assert result is None
        # Should NOT delete expired tokens
        mock_table.delete_item.assert_not_called()


class TestAuthTokenOperations:
    def test_create_auth_token_returns_token(self, mock_table):
        token = db.create_auth_token("test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0
        item = mock_table.put_item.call_args[1]["Item"]
        assert item["pk"].startswith("AUTH#")
        assert item["sk"] == "TOKEN"

    def test_validate_auth_token_returns_email(self, mock_table):
        future_ts = int((datetime.now(timezone.utc) + timedelta(days=15)).timestamp())
        mock_table.get_item.return_value = {
            "Item": {
                "pk": "AUTH#token123",
                "sk": "TOKEN",
                "email": "test@example.com",
                "expires_at": future_ts,
            }
        }
        assert db.validate_auth_token("token123") == "test@example.com"

    def test_validate_auth_token_returns_none_for_expired(self, mock_table):
        past_ts = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
        mock_table.get_item.return_value = {
            "Item": {
                "pk": "AUTH#token123",
                "sk": "TOKEN",
                "email": "test@example.com",
                "expires_at": past_ts,
            }
        }
        assert db.validate_auth_token("token123") is None

    def test_validate_auth_token_returns_none_for_missing(self, mock_table):
        mock_table.get_item.return_value = {}
        assert db.validate_auth_token("missing") is None


class TestDeckOperations:
    def test_get_deck(self, mock_table):
        mock_table.get_item.return_value = {"Item": {"deck_id": "d1"}}
        result = db.get_deck("d1", "test@example.com")
        assert result["deck_id"] == "d1"
        mock_table.get_item.assert_called_once_with(
            Key={"pk": "DECK#d1", "sk": "USER#test@example.com"}
        )

    def test_save_deck(self, mock_table):
        deck = {"pk": "DECK#d1", "sk": "USER#test@example.com"}
        db.save_deck(deck)
        mock_table.put_item.assert_called_once_with(Item=deck)

    def test_draw_card_from_deck_returns_next_card(self):
        deck = {
            "cards_drawn": 0,
            "shuffled_cards": [
                {"rank": "7", "suit": "Hearts"},
                {"rank": "A", "suit": "Spades"},
            ],
            "draw_history": [],
            "completed_at": None,
        }
        card = db.draw_card_from_deck(deck, 2026, 8)
        assert card == {"rank": "7", "suit": "Hearts"}
        assert deck["cards_drawn"] == 1
        assert len(deck["draw_history"]) == 1
        assert deck["draw_history"][0]["year"] == 2026
        assert deck["draw_history"][0]["week"] == 8

    def test_draw_card_returns_none_when_deck_complete(self):
        deck = {
            "cards_drawn": 54,
            "shuffled_cards": [],
            "draw_history": [],
            "completed_at": None,
        }
        assert db.draw_card_from_deck(deck, 2026, 8) is None

    def test_draw_card_marks_complete_on_last_card(self):
        deck = {
            "cards_drawn": 53,
            "shuffled_cards": [{"rank": "A", "suit": "Spades"}] * 54,
            "draw_history": [],
            "completed_at": None,
        }
        db.draw_card_from_deck(deck, 2026, 8)
        assert deck["completed_at"] is not None

    def test_get_card_for_week_finds_match(self):
        deck = {
            "draw_history": [
                {"card": {"rank": "7", "suit": "Hearts"}, "year": 2026, "week": 8, "drawn_at": "2026-02-20"},
            ]
        }
        card = db.get_card_for_week(deck, 2026, 8)
        assert card == {"rank": "7", "suit": "Hearts"}

    def test_get_card_for_week_returns_none_when_no_match(self):
        deck = {
            "draw_history": [
                {"card": {"rank": "7", "suit": "Hearts"}, "year": 2026, "week": 7, "drawn_at": "2026-02-13"},
            ]
        }
        assert db.get_card_for_week(deck, 2026, 8) is None

    def test_get_card_for_week_empty_history(self):
        deck = {"draw_history": []}
        assert db.get_card_for_week(deck, 2026, 8) is None
