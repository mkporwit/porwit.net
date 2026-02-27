"""
Lambda handler for Gunset API
"""
import json
import os
import base64
import boto3
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Optional


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)

from models import (
    create_new_deck_for_user,
    card_with_challenge,
    get_current_week,
)
from db import (
    get_or_create_user,
    get_user,
    update_user_deck,
    create_session,
    verify_session,
    create_auth_token,
    validate_auth_token,
    get_deck,
    save_deck,
    get_user_decks,
    draw_card_from_deck,
    get_card_for_week,
)
from pdf_generator import generate_card_pdf

FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@example.com")

def get_base_url(event):
    """Construct BASE_URL from the incoming request."""
    # Try to get from request context (works in API Gateway)
    request_context = event.get("requestContext", {})
    domain = request_context.get("domainName")
    stage = request_context.get("stage")

    if domain and stage:
        return f"https://{domain}/{stage}"

    # Fallback: construct from environment
    region = os.environ.get("AWS_REGION_NAME", os.environ.get("AWS_REGION", "us-east-1"))
    env = os.environ.get("ENVIRONMENT", "dev")
    # This won't have the API ID, but magic links will still work if user copies from email
    return f"https://api.execute-api.{region}.amazonaws.com/{env}"


def get_cors_origin():
    """Return the allowed CORS origin from FRONTEND_URL, falling back to * for dev."""
    frontend_url = os.environ.get("FRONTEND_URL", "").rstrip("/")
    return frontend_url if frontend_url else "*"

CORS_HEADERS = {
    "Access-Control-Allow-Origin": get_cors_origin(),
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}

def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            **CORS_HEADERS,
        },
        "body": json.dumps(body, cls=DecimalEncoder),
    }

def cors_response() -> dict:
    """Return CORS preflight response."""
    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": "",
    }


def get_auth_email(event: dict) -> Optional[str]:
    """Extract and validate auth token from request."""
    headers = event.get("headers") or {}
    # API Gateway may send headers as lowercase
    auth_header = headers.get("Authorization") or headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return validate_auth_token(token)
    return None


def send_magic_link_email(email: str, token: str):
    """Send magic link email via SES."""
    ses = boto3.client("ses")
    # Link to frontend, which will verify the token
    frontend_url = os.environ.get("FRONTEND_URL", "").rstrip("/")
    magic_link = f"{frontend_url}?token={token}"

    ses.send_email(
        Source=FROM_EMAIL,
        Destination={"ToAddresses": [email]},
        Message={
            "Subject": {"Data": "Your Gunset Login Link"},
            "Body": {
                "Text": {
                    "Data": f"Click here to log in to Gunset:\n\n{magic_link}\n\nThis link expires in 15 minutes."
                },
                "Html": {
                    "Data": f"""
                    <h2>Gunset Login</h2>
                    <p>Click the button below to log in:</p>
                    <p><a href="{magic_link}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Log In to Gunset</a></p>
                    <p>Or copy this link: {magic_link}</p>
                    <p><small>This link expires in 15 minutes.</small></p>
                    """
                },
            },
        },
    )


# --- Route Handlers ---

def handle_auth_request(event: dict) -> dict:
    """POST /auth/request - Request a magic link."""
    try:
        body = json.loads(event.get("body", "{}"))
        email = body.get("email", "").lower().strip()

        if not email or "@" not in email:
            return response(400, {"error": "Valid email required"})

        # Create or get user
        get_or_create_user(email)

        # Create session token
        token = create_session(email)

        # Send email
        send_magic_link_email(email, token)

        return response(200, {"message": "Magic link sent to your email"})

    except Exception as e:
        print(f"Error in auth request: {e}")
        return response(500, {"error": "Failed to send magic link"})


def handle_auth_verify(event: dict) -> dict:
    """GET /auth/verify?token=xxx - Verify magic link and return auth token."""
    params = event.get("queryStringParameters") or {}
    token = params.get("token")

    if not token:
        return response(400, {"error": "Token required"})

    email = verify_session(token)
    if not email:
        return response(401, {"error": "Invalid or expired token"})

    # Create long-lived auth token
    auth_token = create_auth_token(email)

    return response(200, {
        "message": "Logged in successfully",
        "token": auth_token,
        "email": email,
    })


def handle_get_current_card(event: dict) -> dict:
    """GET /card - Get current week's card (draw if not yet drawn)."""
    email = get_auth_email(event)
    if not email:
        return response(401, {"error": "Authentication required"})

    user = get_user(email)
    year, week = get_current_week()

    # Get or create deck
    deck = None
    if user.get("current_deck_id"):
        deck = get_deck(user["current_deck_id"], email)

    # If no deck or deck is complete, create new one
    if not deck or deck.get("completed_at"):
        deck = create_new_deck_for_user(email)
        save_deck(deck)
        update_user_deck(email, deck["deck_id"])

    # Check if already drawn this week
    existing_card = get_card_for_week(deck, year, week)
    if existing_card:
        return response(200, {
            "card": card_with_challenge(existing_card),
            "week": {"year": year, "week": week},
            "already_drawn": True,
            "cards_remaining": 54 - deck["cards_drawn"],
            "deck_progress": f"{deck['cards_drawn']}/54",
        })

    # Draw new card
    card = draw_card_from_deck(deck, year, week)
    if not card:
        # Deck was complete, shouldn't happen due to check above
        return response(500, {"error": "Deck error"})

    save_deck(deck)

    return response(200, {
        "card": card_with_challenge(card),
        "week": {"year": year, "week": week},
        "already_drawn": False,
        "cards_remaining": 54 - deck["cards_drawn"],
        "deck_progress": f"{deck['cards_drawn']}/54",
    })


def handle_get_history(event: dict) -> dict:
    """GET /history - Get draw history for current deck."""
    email = get_auth_email(event)
    if not email:
        return response(401, {"error": "Authentication required"})

    user = get_user(email)

    if not user.get("current_deck_id"):
        return response(200, {"history": [], "deck_progress": "0/54"})

    deck = get_deck(user["current_deck_id"], email)
    if not deck:
        return response(200, {"history": [], "deck_progress": "0/54"})

    history = [
        {
            "card": card_with_challenge(entry["card"]),
            "year": entry["year"],
            "week": entry["week"],
            "drawn_at": entry["drawn_at"],
        }
        for entry in deck["draw_history"]
    ]

    return response(200, {
        "history": history,
        "deck_progress": f"{deck['cards_drawn']}/54",
        "deck_started": deck["created_at"],
        "deck_completed": deck.get("completed_at"),
    })


def handle_get_all_decks(event: dict) -> dict:
    """GET /decks - Get all completed decks (history)."""
    email = get_auth_email(event)
    if not email:
        return response(401, {"error": "Authentication required"})

    decks = get_user_decks(email)

    return response(200, {
        "decks": [
            {
                "deck_id": d["deck_id"],
                "cards_drawn": d["cards_drawn"],
                "created_at": d["created_at"],
                "completed_at": d.get("completed_at"),
            }
            for d in decks
        ],
        "total_decks": len(decks),
        "completed_decks": sum(1 for d in decks if d.get("completed_at")),
    })


def handle_get_deck_detail(event: dict, deck_id: str) -> dict:
    """GET /decks/{deck_id} - Get details of a specific deck."""
    email = get_auth_email(event)
    if not email:
        return response(401, {"error": "Authentication required"})

    if not deck_id:
        return response(400, {"error": "Deck ID required"})

    deck = get_deck(deck_id, email)
    if not deck:
        return response(404, {"error": "Deck not found"})

    return response(200, {
        "deck_id": deck["deck_id"],
        "cards_drawn": deck["cards_drawn"],
        "created_at": deck["created_at"],
        "completed_at": deck.get("completed_at"),
        "history": [
            {
                "card": card_with_challenge(entry["card"]),
                "year": entry["year"],
                "week": entry["week"],
                "drawn_at": entry["drawn_at"],
            }
            for entry in deck["draw_history"]
        ],
    })


# --- PDF Handlers ---

def handle_get_card_pdf(event: dict) -> dict:
    """GET /card/pdf - Download PDF of current week's card."""
    email = get_auth_email(event)
    if not email:
        return response(401, {"error": "Authentication required"})

    user = get_user(email)
    year, week = get_current_week()

    if not user.get("current_deck_id"):
        return response(404, {"error": "No card drawn yet"})

    deck = get_deck(user["current_deck_id"], email)
    if not deck:
        return response(404, {"error": "No card drawn yet"})

    card = get_card_for_week(deck, year, week)
    if not card:
        return response(404, {"error": "No card drawn for this week"})

    week_info = f"Week {week}, {year}"
    pdf_bytes = generate_card_pdf(card["rank"], card["suit"], week_info)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/pdf",
            "Content-Disposition": f'attachment; filename="gunset-week{week}-{year}.pdf"',
            **CORS_HEADERS,
        },
        "body": base64.b64encode(pdf_bytes).decode("utf-8"),
        "isBase64Encoded": True,
    }


def handle_email_card_pdf(event: dict) -> dict:
    """POST /card/email - Email PDF of current week's card."""
    email = get_auth_email(event)
    if not email:
        return response(401, {"error": "Authentication required"})

    user = get_user(email)
    year, week = get_current_week()

    if not user.get("current_deck_id"):
        return response(404, {"error": "No card drawn yet"})

    deck = get_deck(user["current_deck_id"], email)
    if not deck:
        return response(404, {"error": "No card drawn yet"})

    card = get_card_for_week(deck, year, week)
    if not card:
        return response(404, {"error": "No card drawn for this week"})

    week_info = f"Week {week}, {year}"
    pdf_bytes = generate_card_pdf(card["rank"], card["suit"], week_info)

    # Build email with PDF attachment
    challenge = card_with_challenge(card)["challenge"]
    card_name = f"{card['rank']} of {card['suit']}" if card['rank'] != 'JOKER' else f"{card['suit']} Joker"

    msg = MIMEMultipart()
    msg["Subject"] = f"Gunset Challenge - Week {week}, {year}"
    msg["From"] = FROM_EMAIL
    msg["To"] = email

    body_html = f"""
    <h2>Your Gunset Challenge for Week {week}</h2>
    <p><strong>Card:</strong> {card_name}</p>
    <p><strong>Challenge:</strong> {challenge}</p>
    <p>Your card PDF is attached. Good luck!</p>
    <p><small>Progress: {deck['cards_drawn']}/54 cards drawn</small></p>
    """
    msg.attach(MIMEText(body_html, "html"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=f"gunset-week{week}-{year}.pdf")
    msg.attach(attachment)

    ses = boto3.client("ses")
    ses.send_raw_email(
        Source=FROM_EMAIL,
        Destinations=[email],
        RawMessage={"Data": msg.as_string()},
    )

    return response(200, {"message": "Card PDF sent to your email"})


# --- Main Router ---

def lambda_handler(event, context):
    """Main Lambda entry point."""
    try:
        http_method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method"))
        path = event.get("path", event.get("rawPath", "/"))

        # Remove stage prefix if present (/dev or /prod)
        if path.startswith("/prod") or path.startswith("/dev"):
            path = "/" + "/".join(path.split("/")[2:])

        # Remove /api prefix if present (from CloudFront routing)
        if path.startswith("/api/"):
            path = path[4:]  # Remove "/api" prefix, keep the rest
        elif path == "/api":
            path = "/"

        print(f"Request: {http_method} {path}")

        # Route mapping
        if http_method == "POST" and path == "/auth/request":
            return handle_auth_request(event)

        elif http_method == "GET" and path == "/auth/verify":
            return handle_auth_verify(event)

        elif http_method == "GET" and path == "/card":
            return handle_get_current_card(event)

        elif http_method == "GET" and path == "/card/pdf":
            return handle_get_card_pdf(event)

        elif http_method == "POST" and path == "/card/email":
            return handle_email_card_pdf(event)

        elif http_method == "GET" and path == "/history":
            return handle_get_history(event)

        elif http_method == "GET" and path == "/decks":
            return handle_get_all_decks(event)

        elif http_method == "GET" and path.startswith("/decks/"):
            deck_id = path[len("/decks/"):].strip("/")
            return handle_get_deck_detail(event, deck_id)

        elif http_method == "OPTIONS":
            return cors_response()

        return response(404, {"error": "Not found"})

    except Exception as e:
        print(f"Unhandled error: {e}")
        import traceback
        traceback.print_exc()
        return response(500, {"error": "Internal server error"})
