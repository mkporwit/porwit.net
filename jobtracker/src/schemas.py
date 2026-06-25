"""OpenAPI component schemas — single source of truth for data models."""

from typing import Any

SCHEMAS: dict[str, Any] = {
    "Application": {
        "type": "object",
        "properties": {
            "sk": {"type": "string", "description": "Application ID (ULID)"},
            "date": {"type": "string", "format": "date"},
            "company": {"type": "string"},
            "role": {"type": "string"},
            "level": {"type": "string"},
            "status": {"type": "string"},
            "source": {"type": "string"},
            "link": {"type": "string", "format": "uri"},
            "closed": {"type": "boolean"},
            "notes": {"type": "string"},
            "original_week": {"type": "string"},
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"},
        },
    },
    "Company": {
        "type": "object",
        "properties": {
            "sk": {"type": "string", "description": "Company slug"},
            "name": {"type": "string"},
            "sector": {"type": "string"},
            "ats": {
                "type": "string",
                "enum": ["greenhouse", "lever", "ashby", "workable", "pinpoint", "workday"],
            },
            "careers_url": {"type": "string", "format": "uri"},
            "active": {"type": "boolean"},
        },
    },
    "Job": {
        "type": "object",
        "properties": {
            "sk": {"type": "string", "description": "MD5 hash identifier"},
            "company": {"type": "string"},
            "sector": {"type": "string"},
            "title": {"type": "string"},
            "location": {"type": "string"},
            "location_flag": {
                "type": "string",
                "enum": ["good", "bad", "unknown"],
                "description": "Location classification based on preference list",
            },
            "url": {"type": "string", "format": "uri"},
            "first_seen": {"type": "string", "format": "date"},
            "last_seen": {"type": "string", "format": "date"},
            "gone": {
                "type": "boolean",
                "description": "Whether the posting has disappeared from the career page",
            },
            "status": {
                "type": "string",
                "enum": ["new", "reviewed", "applied", "ignored", "poor_match", "gone"],
            },
            "already_applied": {
                "type": "boolean",
                "description": "True if you applied to this exact posting (URL match)",
            },
            "applied_at_company": {
                "type": "boolean",
                "description": "True if you applied to a different role at this company",
            },
        },
    },
}

SECURITY_SCHEMES = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "description": (
            "Use a JWT token from /auth/login, or an API key stored in\n"
            "SSM Parameter Store at /jobtracker/api-key.\n"
        ),
    },
}

ERROR_RESPONSE = {
    "description": "Error response",
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                },
            },
        },
    },
}
