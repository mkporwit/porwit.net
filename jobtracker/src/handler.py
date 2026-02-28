"""Lambda handler for JobTracker API."""

import os
import json
import inspect
import re
from datetime import datetime, timezone

from ulid import ULID

import db
import auth
import routes
import schemas

VALID_ATS = set(schemas.SCHEMAS["Company"]["properties"]["ats"]["enum"])

FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")

# Compile route patterns once at import time
_COMPILED_ROUTES = []
for _route in routes.ROUTES:
    _pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", _route.path)
    _COMPILED_ROUTES.append((re.compile(f"^{_pattern}$"), _route))


def lambda_handler(event, context):
    """Main Lambda entry point — routes API Gateway requests."""
    method = event.get("httpMethod", "GET")
    path = event.get("path", "/")

    # Strip stage prefix (/dev, /prod) and /api prefix
    path = re.sub(r"^/(dev|prod)", "", path)
    path = re.sub(r"^/api", "", path)
    path = path.rstrip("/") or "/"

    # CORS preflight
    if method == "OPTIONS":
        return cors_response()

    # Route to handlers via route table
    try:
        for regex, route in _COMPILED_ROUTES:
            if route.method != method:
                continue
            match = regex.match(path)
            if not match:
                continue

            # Auth check
            if route.auth:
                is_authed, identity = auth.authenticate(event)
                if not is_authed:
                    return error_response(401, identity)

            handler_fn = globals()[route.handler]
            groups = match.groupdict()
            # Call handler with the right signature: (event), (param, event), or (param)
            if groups:
                sig = inspect.signature(handler_fn)
                if len(sig.parameters) > len(groups):
                    return handler_fn(*groups.values(), event)
                return handler_fn(*groups.values())
            return handler_fn(event)

        return error_response(404, f"Not found: {method} {path}")

    except Exception as e:
        print(f"Error handling {method} {path}: {e}")
        return error_response(500, str(e))


# --- Auth ---


def handle_login(event):
    body = parse_body(event)
    username = body.get("username", "")
    password = body.get("password", "")

    if not auth.verify_password(username, password):
        return error_response(401, "Invalid credentials")

    token = auth.create_jwt(username)
    return json_response(200, {
        "token": token,
        "username": username,
    })


# --- Applications ---


def handle_list_applications(event):
    params = event.get("queryStringParameters") or {}
    filters = {}
    for key in ("company", "status", "level", "source", "date_from", "date_to"):
        if key in params:
            filters[key] = params[key]
    limit = int(params.get("limit", 50))
    result = db.list_applications(filters=filters if filters else None, limit=limit)
    return json_response(200, result)


def handle_create_application(event):
    body = parse_body(event)
    app_id = str(ULID())
    required = ("date", "company", "role")
    for field in required:
        if field not in body:
            return error_response(400, f"Missing required field: {field}")
    item = db.put_application(app_id, body)
    return json_response(201, {"id": app_id, "application": item})


def handle_update_application(app_id, event):
    existing = db.get_application(app_id)
    if not existing:
        return error_response(404, f"Application not found: {app_id}")
    body = parse_body(event)
    updated = db.update_application(app_id, body)
    return json_response(200, {"application": updated})


def handle_delete_application(app_id):
    existing = db.get_application(app_id)
    if not existing:
        return error_response(404, f"Application not found: {app_id}")
    db.delete_application(app_id)
    return json_response(200, {"deleted": app_id})


# --- Search ---


def handle_search(event):
    params = event.get("queryStringParameters") or {}
    company = params.get("company", "")
    if not company:
        return error_response(400, "Missing 'company' parameter")
    result = db.search_applications(company)
    return json_response(200, result)


# --- Monitor ---


def handle_monitor_results(event):
    params = event.get("queryStringParameters") or {}
    filters = {}
    for key in ("sector", "status", "company"):
        if key in params:
            filters[key] = params[key]

    jobs = db.list_jobs(filters=filters if filters else None)
    # Filter out gone jobs unless specifically requested
    if "status" not in filters:
        jobs = [j for j in jobs if not j.get("gone", False)]

    # Cross-reference with applications
    app_result = db.list_applications(limit=None)
    applied_links = {a.get("link", "").lower() for a in app_result["applications"] if a.get("link")}
    applied_companies = [a.get("company", "").lower() for a in app_result["applications"]]
    for job in jobs:
        job_url = job.get("url", "").lower()
        job_company = job.get("company", "").lower()
        # Exact URL match = applied to this specific role
        job["already_applied"] = bool(job_url and job_url in applied_links)
        # Company match = applied to a different role at this company
        job["applied_at_company"] = not job["already_applied"] and any(
            job_company in ac or ac in job_company
            for ac in applied_companies if ac
        )

    # Get last scan info
    scans = db.list_scan_logs(limit=1)
    last_scan = scans[0]["sk"] if scans else None

    active_jobs = [j for j in jobs if not j.get("gone", False)]
    new_jobs = [j for j in active_jobs if j.get("status") == "new"]

    return json_response(200, {
        "last_scan": last_scan,
        "total_active": len(active_jobs),
        "new_since_last": len(new_jobs),
        "jobs": jobs,
    })


def handle_list_companies(event):
    companies = db.list_companies()
    return json_response(200, {"companies": companies})


def handle_create_company(event):
    body = parse_body(event)
    slug = body.get("slug", "")
    if not slug:
        return error_response(400, "Missing 'slug'")
    ats = body.get("ats", "")
    if not ats or ats not in VALID_ATS:
        return error_response(400, f"'ats' is required and must be one of: {', '.join(sorted(VALID_ATS))}")
    item = db.put_company(slug, body)
    return json_response(201, {"company": item})


def handle_update_company(slug, event):
    existing = db.get_company(slug)
    if not existing:
        return error_response(404, f"Company not found: {slug}")
    body = parse_body(event)
    if "ats" in body and body["ats"] not in VALID_ATS:
        return error_response(400, f"'ats' must be one of: {', '.join(sorted(VALID_ATS))}")
    updated = db.update_company(slug, body)
    return json_response(200, {"company": updated})


def handle_delete_company(slug):
    existing = db.get_company(slug)
    if not existing:
        return error_response(404, f"Company not found: {slug}")
    db.delete_company(slug)
    return json_response(200, {"deleted": slug})


def handle_update_job(job_hash, event):
    existing = db.get_job(job_hash)
    if not existing:
        return error_response(404, f"Job not found: {job_hash}")
    body = parse_body(event)
    updated = db.update_job(job_hash, body)
    return json_response(200, {"job": updated})


def handle_trigger_scan(event):
    """Trigger a scan by invoking the scanner Lambda."""
    import boto3

    function_name = os.environ.get("SCANNER_FUNCTION_NAME", "jobtracker-scanner")

    client = boto3.client("lambda")
    client.invoke(
        FunctionName=function_name,
        InvocationType="Event",  # async
    )
    return json_response(202, {"message": "Scan triggered"})


# --- Stats ---


def handle_stats(event):
    app_result = db.list_applications(limit=None)
    apps = app_result["applications"]

    now = datetime.now(timezone.utc)
    this_month = now.strftime("%Y-%m")

    by_status = {}
    by_level = {}
    month_count = 0
    interview_statuses = {
        "recruiter screen", "recruiter call", "recruiter interview",
        "recruiter conversation", "recruiting interview", "recruiter discussion",
        "hiring manager interview", "interview", "technical interview",
        "system design interview", "behavioral interview", "architecture interview",
        "product interview", "onsite coding interview", "cto interview",
    }
    interview_count = 0

    for app in apps:
        status = app.get("status", "Unknown")
        level = app.get("level", "Unknown")
        by_status[status] = by_status.get(status, 0) + 1
        by_level[level] = by_level.get(level, 0) + 1
        if app.get("date", "").startswith(this_month):
            month_count += 1
        if status.lower() in interview_statuses:
            interview_count += 1

    total = len(apps)
    interview_rate = interview_count / total if total > 0 else 0

    # Monitor stats
    companies = db.list_companies()
    jobs = db.list_jobs()
    active_jobs = [j for j in jobs if not j.get("gone", False)]
    new_jobs = [j for j in active_jobs if j.get("status") == "new"]

    # New this week
    week_ago = (now - __import__("datetime").timedelta(days=7)).strftime("%Y-%m-%d")
    new_this_week = [
        j for j in new_jobs if j.get("first_seen", "") >= week_ago
    ]

    return json_response(200, {
        "total_applications": total,
        "this_month": month_count,
        "by_status": by_status,
        "by_level": by_level,
        "interview_rate": round(interview_rate, 3),
        "monitor": {
            "companies_tracked": len(companies),
            "active_matches": len(active_jobs),
            "new_this_week": len(new_this_week),
        },
    })


# --- Import ---


def handle_import(event):
    """Handle Excel file import via base64-encoded body."""
    import base64
    import io

    try:
        import openpyxl
    except ImportError:
        return error_response(500, "openpyxl not available in Lambda — use the import script instead")

    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    else:
        body = body.encode()

    wb = openpyxl.load_workbook(io.BytesIO(body))
    ws = wb.active

    imported = 0
    skipped = 0
    errors = []

    for row in ws.iter_rows(min_row=2, values_only=False):
        try:
            company = row[1].value
            if not company:
                skipped += 1
                continue

            date_val = row[0].value
            if hasattr(date_val, "strftime"):
                date_str = date_val.strftime("%Y-%m-%d")
            else:
                date_str = str(date_val) if date_val else ""

            status = str(row[4].value or "Applied").strip()
            # Fix data entry errors where URLs ended up in status
            if status.startswith("http"):
                status = "Applied"

            app_id = str(ULID())
            data = {
                "date": date_str,
                "company": str(company).strip(),
                "role": str(row[2].value or "").strip(),
                "level": str(row[3].value or "").strip(),
                "status": status,
                "source": str(row[5].value or "").strip(),
                "link": str(row[6].value or "").strip(),
                "closed": bool(row[7].value) if row[7].value else False,
                "original_week": str(row[8].value or "").strip(),
                "notes": str(row[9].value or "").strip(),
            }
            # Remove empty string values
            data = {k: v for k, v in data.items() if v not in ("", "None")}

            db.put_application(app_id, data)
            imported += 1
        except Exception as e:
            errors.append(f"Row {row[0].row}: {e}")

    return json_response(200, {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    })


# --- Response Helpers ---


def cors_headers():
    origin = FRONTEND_URL if FRONTEND_URL != "*" else "*"
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS",
    }


def cors_response():
    return {"statusCode": 200, "headers": cors_headers(), "body": ""}


def json_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            **cors_headers(),
        },
        "body": json.dumps(body, default=db.decimal_default),
    }


def error_response(status_code, message):
    return json_response(status_code, {"error": message})


def parse_body(event):
    body = event.get("body", "")
    if not body:
        return {}
    if event.get("isBase64Encoded"):
        import base64
        body = base64.b64decode(body).decode()
    try:
        return json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return {}
