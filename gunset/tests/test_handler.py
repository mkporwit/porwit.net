"""Tests for handler.py - routing, auth, and request handling."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

os.environ.setdefault("DYNAMODB_TABLE", "gunset-test")
os.environ.setdefault("FROM_EMAIL", "test@example.com")

import json
import pytest
from unittest.mock import patch, MagicMock

import handler


def make_event(method="GET", path="/", body=None, headers=None, query_params=None):
    """Build a minimal API Gateway proxy event."""
    event = {
        "httpMethod": method,
        "path": path,
        "headers": headers or {},
        "queryStringParameters": query_params,
        "body": json.dumps(body) if body is not None else None,
        "requestContext": {},
    }
    return event


class TestRouting:
    def test_options_returns_cors(self):
        event = make_event("OPTIONS", "/anything")
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in result["headers"]

    def test_unknown_route_returns_404(self):
        event = make_event("GET", "/nonexistent")
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 404

    def test_strips_stage_prefix(self):
        event = make_event("GET", "/dev/nonexistent")
        result = handler.lambda_handler(event, None)
        # Should strip /dev and try /nonexistent -> 404
        assert result["statusCode"] == 404

    def test_strips_api_prefix(self):
        event = make_event("GET", "/api/nonexistent")
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 404

    @patch("handler.validate_auth_token", return_value=None)
    def test_auth_required_routes_return_401(self, mock_validate):
        auth_routes = [
            ("GET", "/card"),
            ("GET", "/card/pdf"),
            ("POST", "/card/email"),
            ("GET", "/history"),
            ("GET", "/decks"),
            ("GET", "/decks/some-id"),
        ]
        for method, path in auth_routes:
            event = make_event(method, path)
            result = handler.lambda_handler(event, None)
            body = json.loads(result["body"])
            assert result["statusCode"] == 401, f"{method} {path} should require auth"
            assert "error" in body


class TestAuthRequest:
    @patch("handler.send_magic_link_email")
    @patch("handler.create_session", return_value="test-token")
    @patch("handler.get_or_create_user")
    def test_valid_email_sends_magic_link(self, mock_user, mock_session, mock_email):
        event = make_event("POST", "/auth/request", body={"email": "test@example.com"})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 200
        mock_user.assert_called_once_with("test@example.com")
        mock_session.assert_called_once_with("test@example.com")
        mock_email.assert_called_once()

    @patch("handler.send_magic_link_email")
    @patch("handler.create_session", return_value="tok")
    @patch("handler.get_or_create_user")
    def test_ses_error_does_not_leak_email_to_logs(self, mock_user, mock_session, mock_email, capsys):
        from botocore.exceptions import ClientError
        leak = "attacker@evil.com"
        mock_email.side_effect = ClientError(
            {"Error": {"Code": "MessageRejected", "Message": f"not verified: {leak}"},
             "ResponseMetadata": {"RequestId": "req-123"}},
            "SendEmail",
        )
        event = make_event("POST", "/auth/request", body={"email": leak})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 500
        out = capsys.readouterr().out
        assert leak not in out              # no PII leak
        assert "MessageRejected" in out     # operational signal kept

    @patch("handler.create_session")
    @patch("handler.get_or_create_user")
    def test_dynamodb_error_keeps_full_traceback(self, mock_user, mock_session, capsys):
        # A non-SES ClientError (DynamoDB) must NOT take the redacted SES branch;
        # it keeps the full traceback for diagnostics.
        from botocore.exceptions import ClientError
        mock_session.side_effect = ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "throttled"}},
            "PutItem",
        )
        event = make_event("POST", "/auth/request", body={"email": "u@example.com"})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 500
        captured = capsys.readouterr()
        assert "Traceback" in captured.err
        assert "SES ClientError" not in captured.out

    def test_missing_email_returns_400(self):
        event = make_event("POST", "/auth/request", body={})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 400

    def test_invalid_email_returns_400(self):
        event = make_event("POST", "/auth/request", body={"email": "notanemail"})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 400

    @patch("handler.send_magic_link_email")
    @patch("handler.create_session", return_value="tok")
    @patch("handler.get_or_create_user")
    def test_email_is_lowercased_and_stripped(self, mock_user, mock_session, mock_email):
        event = make_event("POST", "/auth/request", body={"email": "  Test@Example.COM  "})
        handler.lambda_handler(event, None)
        mock_user.assert_called_once_with("test@example.com")


class TestAuthVerify:
    def test_missing_token_returns_400(self):
        event = make_event("GET", "/auth/verify")
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 400

    @patch("handler.create_auth_token", return_value="auth-token-123")
    @patch("handler.verify_session", return_value="test@example.com")
    def test_valid_token_returns_auth_token(self, mock_verify, mock_create):
        event = make_event("GET", "/auth/verify", query_params={"token": "magic-link-token"})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["token"] == "auth-token-123"
        assert body["email"] == "test@example.com"

    @patch("handler.verify_session", return_value=None)
    def test_invalid_token_returns_401(self, mock_verify):
        event = make_event("GET", "/auth/verify", query_params={"token": "bad-token"})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 401


class TestGetCurrentCard:
    @patch("handler.save_deck")
    @patch("handler.draw_card_from_deck", return_value={"rank": "7", "suit": "Hearts"})
    @patch("handler.get_card_for_week", return_value=None)
    @patch("handler.get_deck", return_value={
        "deck_id": "d1", "cards_drawn": 0, "draw_history": [], "completed_at": None
    })
    @patch("handler.get_current_week", return_value=(2026, 8))
    @patch("handler.get_user", return_value={"current_deck_id": "d1"})
    @patch("handler.validate_auth_token", return_value="test@example.com")
    def test_draws_new_card(self, *mocks):
        event = make_event("GET", "/card", headers={"Authorization": "Bearer tok"})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["card"]["rank"] == "7"
        assert body["already_drawn"] is False

    @patch("handler.get_card_for_week", return_value={"rank": "A", "suit": "Spades"})
    @patch("handler.get_deck", return_value={
        "deck_id": "d1", "cards_drawn": 5, "draw_history": [], "completed_at": None
    })
    @patch("handler.get_current_week", return_value=(2026, 8))
    @patch("handler.get_user", return_value={"current_deck_id": "d1"})
    @patch("handler.validate_auth_token", return_value="test@example.com")
    def test_returns_existing_card(self, *mocks):
        event = make_event("GET", "/card", headers={"Authorization": "Bearer tok"})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["card"]["rank"] == "A"
        assert body["already_drawn"] is True


class TestDeckDetail:
    @patch("handler.get_deck", return_value={
        "deck_id": "d1", "cards_drawn": 2, "created_at": "2026-01-01",
        "completed_at": None, "draw_history": []
    })
    @patch("handler.validate_auth_token", return_value="test@example.com")
    def test_returns_deck_detail(self, mock_auth, mock_deck):
        event = make_event("GET", "/decks/d1", headers={"Authorization": "Bearer tok"})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["deck_id"] == "d1"

    @patch("handler.get_deck", return_value=None)
    @patch("handler.validate_auth_token", return_value="test@example.com")
    def test_returns_404_for_missing_deck(self, mock_auth, mock_deck):
        event = make_event("GET", "/decks/nonexistent", headers={"Authorization": "Bearer tok"})
        result = handler.lambda_handler(event, None)
        assert result["statusCode"] == 404

    @patch("handler.validate_auth_token", return_value="test@example.com")
    def test_extracts_deck_id_from_path(self, mock_auth):
        """Verify deck_id is correctly parsed from /{proxy+} path."""
        with patch("handler.get_deck", return_value=None) as mock_get:
            event = make_event("GET", "/decks/abc-123-def", headers={"Authorization": "Bearer tok"})
            handler.lambda_handler(event, None)
            mock_get.assert_called_once_with("abc-123-def", "test@example.com")


class TestGetAuthEmail:
    @patch("handler.validate_auth_token", return_value="test@example.com")
    def test_extracts_bearer_token(self, mock_validate):
        event = {"headers": {"Authorization": "Bearer my-token"}}
        result = handler.get_auth_email(event)
        assert result == "test@example.com"
        mock_validate.assert_called_once_with("my-token")

    @patch("handler.validate_auth_token", return_value="test@example.com")
    def test_handles_lowercase_header(self, mock_validate):
        event = {"headers": {"authorization": "Bearer my-token"}}
        result = handler.get_auth_email(event)
        assert result == "test@example.com"

    def test_returns_none_without_auth_header(self):
        event = {"headers": {}}
        result = handler.get_auth_email(event)
        assert result is None

    def test_returns_none_with_empty_headers(self):
        event = {"headers": None}
        result = handler.get_auth_email(event)
        assert result is None

    def test_returns_none_for_non_bearer(self):
        event = {"headers": {"Authorization": "Basic abc123"}}
        result = handler.get_auth_email(event)
        assert result is None


class TestCorsHeaders:
    def test_response_includes_cors_headers(self):
        result = handler.response(200, {"ok": True})
        assert "Access-Control-Allow-Origin" in result["headers"]
        assert "Access-Control-Allow-Methods" in result["headers"]
        assert "Access-Control-Allow-Headers" in result["headers"]

    def test_cors_response_includes_headers(self):
        result = handler.cors_response()
        assert result["statusCode"] == 200
        assert "Access-Control-Allow-Origin" in result["headers"]


class TestDecimalEncoder:
    def test_encodes_integer_decimal(self):
        from decimal import Decimal
        result = json.dumps({"n": Decimal("42")}, cls=handler.DecimalEncoder)
        assert '"n": 42' in result

    def test_encodes_float_decimal(self):
        from decimal import Decimal
        result = json.dumps({"n": Decimal("3.14")}, cls=handler.DecimalEncoder)
        assert '"n": 3.14' in result
