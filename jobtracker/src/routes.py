"""Route registry — single source of truth for HTTP routing and OpenAPI spec."""

from collections import namedtuple

Route = namedtuple("Route", [
    "method",       # HTTP method (GET, POST, PATCH, DELETE)
    "path",         # URL pattern, e.g. /applications/{id}
    "handler",      # handler function name in handler.py
    "auth",         # whether auth is required
    "summary",      # OpenAPI summary
    "description",  # OpenAPI description (optional, longer text)
    "parameters",   # list of OpenAPI parameter dicts
    "request_body", # OpenAPI requestBody dict or None
    "responses",    # dict of status code str -> OpenAPI response dict
])
Route.__new__.__defaults__ = (True, "", None, [], None, {})

ROUTES = [
    # --- Auth ---
    Route(
        method="POST",
        path="/auth/login",
        handler="handle_login",
        auth=False,
        summary="Log in and get a JWT token",
        parameters=[],
        request_body={
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["username", "password"],
                        "properties": {
                            "username": {"type": "string"},
                            "password": {"type": "string"},
                        },
                    },
                },
            },
        },
        responses={
            "200": {
                "description": "Login successful",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "token": {
                                    "type": "string",
                                    "description": "JWT token (valid for 30 days)",
                                },
                                "username": {"type": "string"},
                            },
                        },
                    },
                },
            },
            "401": {"$ref": "#/components/responses/Error"},
        },
    ),

    # --- Applications ---
    Route(
        method="GET",
        path="/applications",
        handler="handle_list_applications",
        summary="List job applications",
        parameters=[
            {
                "name": "company", "in": "query",
                "schema": {"type": "string"},
                "description": "Filter by company name (case-insensitive substring)",
            },
            {
                "name": "status", "in": "query",
                "schema": {"type": "string"},
                "description": "Filter by status (case-insensitive substring)",
            },
            {
                "name": "level", "in": "query",
                "schema": {"type": "string"},
                "description": "Filter by level",
            },
            {
                "name": "source", "in": "query",
                "schema": {"type": "string"},
                "description": "Filter by source",
            },
            {
                "name": "date_from", "in": "query",
                "schema": {"type": "string", "format": "date"},
                "description": "Filter applications on or after this date (YYYY-MM-DD)",
            },
            {
                "name": "date_to", "in": "query",
                "schema": {"type": "string", "format": "date"},
                "description": "Filter applications on or before this date (YYYY-MM-DD)",
            },
            {
                "name": "limit", "in": "query",
                "schema": {"type": "integer", "default": 50},
                "description": "Max number of applications to return",
            },
        ],
        responses={
            "200": {
                "description": "List of applications",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "count": {
                                    "type": "integer",
                                    "description": "Total matching applications (before limit)",
                                },
                                "applications": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Application"},
                                },
                            },
                        },
                    },
                },
            },
        },
    ),
    Route(
        method="POST",
        path="/applications",
        handler="handle_create_application",
        summary="Create a new job application",
        request_body={
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["date", "company", "role"],
                        "properties": {
                            "date": {
                                "type": "string", "format": "date",
                                "description": "Application date (YYYY-MM-DD)",
                            },
                            "company": {"type": "string"},
                            "role": {"type": "string"},
                            "level": {
                                "type": "string",
                                "description": "Seniority level (e.g. Director, VP, Senior EM)",
                            },
                            "status": {
                                "type": "string",
                                "description": "Application status (e.g. Applied, Interview, Rejected, Offer)",
                            },
                            "source": {
                                "type": "string",
                                "description": "Where the job was found (e.g. LinkedIn, Referral)",
                            },
                            "link": {
                                "type": "string", "format": "uri",
                                "description": "URL of the job posting",
                            },
                            "notes": {"type": "string"},
                        },
                    },
                },
            },
        },
        responses={
            "201": {
                "description": "Application created",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "ULID of the new application",
                                },
                                "application": {
                                    "$ref": "#/components/schemas/Application",
                                },
                            },
                        },
                    },
                },
            },
            "400": {"$ref": "#/components/responses/Error"},
        },
    ),
    Route(
        method="PATCH",
        path="/applications/{id}",
        handler="handle_update_application",
        summary="Update a job application",
        parameters=[
            {
                "name": "id", "in": "path", "required": True,
                "schema": {"type": "string"},
                "description": "Application ULID",
            },
        ],
        request_body={
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "description": "Fields to update (any Application field)",
                        "properties": {
                            "status": {"type": "string"},
                            "level": {"type": "string"},
                            "notes": {"type": "string"},
                            "link": {"type": "string"},
                            "closed": {"type": "boolean"},
                        },
                    },
                },
            },
        },
        responses={
            "200": {
                "description": "Application updated",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "application": {
                                    "$ref": "#/components/schemas/Application",
                                },
                            },
                        },
                    },
                },
            },
            "404": {"$ref": "#/components/responses/Error"},
        },
    ),
    Route(
        method="DELETE",
        path="/applications/{id}",
        handler="handle_delete_application",
        summary="Delete a job application",
        parameters=[
            {
                "name": "id", "in": "path", "required": True,
                "schema": {"type": "string"},
                "description": "Application ULID",
            },
        ],
        responses={
            "200": {
                "description": "Application deleted",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "deleted": {
                                    "type": "string",
                                    "description": "ID of the deleted application",
                                },
                            },
                        },
                    },
                },
            },
            "404": {"$ref": "#/components/responses/Error"},
        },
    ),

    # --- Search ---
    Route(
        method="GET",
        path="/search",
        handler="handle_search",
        summary="Search applications by company name",
        parameters=[
            {
                "name": "company", "in": "query", "required": True,
                "schema": {"type": "string"},
                "description": "Company name to search (case-insensitive substring match)",
            },
        ],
        responses={
            "200": {
                "description": "Matching applications",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "count": {"type": "integer"},
                                "applications": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Application"},
                                },
                            },
                        },
                    },
                },
            },
            "400": {"$ref": "#/components/responses/Error"},
        },
    ),

    # --- Stats ---
    Route(
        method="GET",
        path="/stats",
        handler="handle_stats",
        summary="Get application and monitor statistics",
        responses={
            "200": {
                "description": "Aggregate statistics",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "total_applications": {"type": "integer"},
                                "this_month": {
                                    "type": "integer",
                                    "description": "Applications submitted this calendar month",
                                },
                                "by_status": {
                                    "type": "object",
                                    "additionalProperties": {"type": "integer"},
                                    "description": "Count of applications grouped by status",
                                },
                                "by_level": {
                                    "type": "object",
                                    "additionalProperties": {"type": "integer"},
                                    "description": "Count of applications grouped by level",
                                },
                                "interview_rate": {
                                    "type": "number", "format": "float",
                                    "description": "Fraction of applications that reached interview stage",
                                },
                                "monitor": {
                                    "type": "object",
                                    "properties": {
                                        "companies_tracked": {"type": "integer"},
                                        "active_matches": {
                                            "type": "integer",
                                            "description": "Active job postings matching title filters",
                                        },
                                        "new_this_week": {"type": "integer"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    ),

    # --- Monitor: Companies ---
    Route(
        method="GET",
        path="/monitor/companies",
        handler="handle_list_companies",
        summary="List monitored companies",
        responses={
            "200": {
                "description": "All monitored companies",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "companies": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Company"},
                                },
                            },
                        },
                    },
                },
            },
        },
    ),
    Route(
        method="POST",
        path="/monitor/companies",
        handler="handle_create_company",
        summary="Add a company to monitor",
        request_body={
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["slug"],
                        "properties": {
                            "slug": {
                                "type": "string",
                                "description": "Unique URL-safe identifier",
                            },
                            "name": {"type": "string"},
                            "sector": {
                                "type": "string",
                                "description": "Industry sector (e.g. Healthcare, Fintech, Dev Tools)",
                            },
                            "ats": {
                                "type": "string",
                                "enum": ["greenhouse", "lever", "ashby", "workable", "pinpoint", "workday"],
                                "description": "Applicant tracking system used by the company",
                            },
                            "careers_url": {
                                "type": "string", "format": "uri",
                                "description": "URL of the company's job board page",
                            },
                            "active": {
                                "type": "boolean", "default": True,
                                "description": "Whether to include in daily scans",
                            },
                        },
                    },
                },
            },
        },
        responses={
            "201": {
                "description": "Company added",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "company": {
                                    "$ref": "#/components/schemas/Company",
                                },
                            },
                        },
                    },
                },
            },
            "400": {"$ref": "#/components/responses/Error"},
        },
    ),
    Route(
        method="PATCH",
        path="/monitor/companies/{slug}",
        handler="handle_update_company",
        summary="Update a monitored company",
        parameters=[
            {
                "name": "slug", "in": "path", "required": True,
                "schema": {"type": "string"},
            },
        ],
        request_body={
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "description": "Fields to update (any Company field)",
                        "properties": {
                            "name": {"type": "string"},
                            "sector": {"type": "string"},
                            "ats": {"type": "string"},
                            "careers_url": {"type": "string"},
                            "active": {"type": "boolean"},
                        },
                    },
                },
            },
        },
        responses={
            "200": {
                "description": "Company updated",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "company": {
                                    "$ref": "#/components/schemas/Company",
                                },
                            },
                        },
                    },
                },
            },
            "404": {"$ref": "#/components/responses/Error"},
        },
    ),
    Route(
        method="DELETE",
        path="/monitor/companies/{slug}",
        handler="handle_delete_company",
        summary="Delete a monitored company",
        parameters=[
            {
                "name": "slug", "in": "path", "required": True,
                "schema": {"type": "string"},
            },
        ],
        responses={
            "200": {
                "description": "Company deleted",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "deleted": {
                                    "type": "string",
                                    "description": "Slug of the deleted company",
                                },
                            },
                        },
                    },
                },
            },
            "404": {"$ref": "#/components/responses/Error"},
        },
    ),

    # --- Monitor: Results ---
    Route(
        method="GET",
        path="/monitor/results",
        handler="handle_monitor_results",
        summary="Get scanner results (matched job postings)",
        description=(
            "Returns job postings found by the career page scanner that match\n"
            "engineering leadership title patterns. Each job is cross-referenced\n"
            "against your applications to flag duplicates.\n"
        ),
        parameters=[
            {
                "name": "sector", "in": "query",
                "schema": {"type": "string"},
                "description": "Filter by sector",
            },
            {
                "name": "status", "in": "query",
                "schema": {"type": "string"},
                "description": "Filter by job status (new, reviewed, applied, gone)",
            },
            {
                "name": "company", "in": "query",
                "schema": {"type": "string"},
                "description": "Filter by company name",
            },
        ],
        responses={
            "200": {
                "description": "Scanner results",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "last_scan": {
                                    "type": "string", "format": "date-time",
                                    "nullable": True,
                                    "description": "Timestamp of the most recent scan",
                                },
                                "total_active": {"type": "integer"},
                                "new_since_last": {"type": "integer"},
                                "by_status": {
                                    "type": "object",
                                    "additionalProperties": {"type": "integer"},
                                    "description": "Count of active jobs grouped by status",
                                },
                                "already_applied": {
                                    "type": "integer",
                                    "description": "Count of active jobs matching an application URL",
                                },
                                "jobs": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Job"},
                                },
                            },
                        },
                    },
                },
            },
        },
    ),

    # --- Monitor: Jobs ---
    Route(
        method="PATCH",
        path="/monitor/jobs/{hash}",
        handler="handle_update_job",
        summary="Update a scanned job posting",
        description="Typically used to change status (e.g. from \"new\" to \"reviewed\")",
        parameters=[
            {
                "name": "hash", "in": "path", "required": True,
                "schema": {"type": "string"},
                "description": "MD5 hash identifier of the job posting",
            },
        ],
        request_body={
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["new", "reviewed", "applied", "ignored", "poor_match", "gone"],
                            },
                            "notes": {"type": "string"},
                        },
                    },
                },
            },
        },
        responses={
            "200": {
                "description": "Job updated",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "job": {"$ref": "#/components/schemas/Job"},
                            },
                        },
                    },
                },
            },
            "404": {"$ref": "#/components/responses/Error"},
        },
    ),

    # --- Monitor: Scan ---
    Route(
        method="POST",
        path="/monitor/scan",
        handler="handle_trigger_scan",
        summary="Trigger a career page scan",
        description=(
            "Asynchronously invokes the scanner Lambda to crawl all active\n"
            "company career pages. Results appear in /monitor/results.\n"
        ),
        responses={
            "202": {
                "description": "Scan triggered",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "example": "Scan triggered",
                                },
                            },
                        },
                    },
                },
            },
        },
    ),

    # --- Import ---
    Route(
        method="POST",
        path="/import",
        handler="handle_import",
        summary="Import applications from Excel file",
        description="Upload a base64-encoded Excel file to bulk-import applications.",
        request_body={
            "required": True,
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
        },
        responses={
            "200": {
                "description": "Import results",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "imported": {"type": "integer"},
                                "skipped": {"type": "integer"},
                                "errors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        },
    ),
]
