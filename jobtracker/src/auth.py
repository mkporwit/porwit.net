"""Authentication for JobTracker — JWT sessions + API key."""

import os
from datetime import datetime, timezone, timedelta

import boto3
import jwt
import bcrypt as _bcrypt

SSM_PREFIX = os.environ.get("SSM_PREFIX", "/jobtracker")
JWT_EXPIRY_DAYS = 30

# Cache secrets after first load
_secrets = None


def _load_secrets():
    """Load secrets from SSM Parameter Store (cached for Lambda lifetime)."""
    global _secrets
    if _secrets is not None:
        return _secrets

    ssm = boto3.client("ssm")
    resp = ssm.get_parameters_by_path(
        Path=SSM_PREFIX,
        WithDecryption=True,
    )
    params = {}
    for p in resp["Parameters"]:
        # /jobtracker/api-key -> api-key
        key = p["Name"].split("/")[-1]
        params[key] = p["Value"]

    _secrets = {
        "api_key": params.get("api-key", ""),
        "admin_user": params.get("admin-user", "marcin"),
        "admin_pass_hash": params.get("admin-pass-hash", ""),
        "jwt_secret": params.get("jwt-secret", "dev-secret-change-me"),
    }
    return _secrets


def verify_password(username, password):
    """Check username/password against configured credentials."""
    secrets = _load_secrets()
    if username != secrets["admin_user"]:
        return False
    if not secrets["admin_pass_hash"]:
        return False
    return _bcrypt.checkpw(password.encode(), secrets["admin_pass_hash"].encode())


def create_jwt(username):
    """Create a JWT token for the web UI session."""
    secrets = _load_secrets()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRY_DAYS),
    }
    return jwt.encode(payload, secrets["jwt_secret"], algorithm="HS256")


def verify_jwt(token):
    """Verify and decode a JWT token. Returns payload or None."""
    secrets = _load_secrets()
    try:
        payload = jwt.decode(token, secrets["jwt_secret"], algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def authenticate(event):
    """Authenticate a request. Returns (is_authenticated, username_or_error).

    Accepts either:
    - Bearer {API_KEY} — for Claude/external API access
    - Bearer {JWT} — for web UI session
    """
    secrets = _load_secrets()
    auth_header = _get_header(event, "authorization")
    if not auth_header:
        return False, "Missing Authorization header"

    if not auth_header.startswith("Bearer "):
        return False, "Invalid Authorization format"

    token = auth_header[7:]

    # Check API key first
    if secrets["api_key"] and token == secrets["api_key"]:
        return True, "api"

    # Try JWT
    payload = verify_jwt(token)
    if payload:
        return True, payload["sub"]

    return False, "Invalid token"


def _get_header(event, header_name):
    """Get a header value from API Gateway event (case-insensitive)."""
    headers = event.get("headers") or {}
    for k, v in headers.items():
        if k.lower() == header_name.lower():
            return v
    return None
