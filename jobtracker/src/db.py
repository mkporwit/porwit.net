"""DynamoDB operations for JobTracker."""

import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "jobtracker-dev")

_table = None


def get_table():
    global _table
    if _table is None:
        dynamodb = boto3.resource("dynamodb")
        _table = dynamodb.Table(TABLE_NAME)
    return _table


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# --- Applications ---


def put_application(app_id, data):
    """Create or fully replace an application item."""
    item = {
        "pk": "APPLICATION",
        "sk": app_id,
        **data,
        "created_at": data.get("created_at", now_iso()),
        "updated_at": now_iso(),
    }
    get_table().put_item(Item=item)
    return item


def get_application(app_id):
    resp = get_table().get_item(Key={"pk": "APPLICATION", "sk": app_id})
    return resp.get("Item")


def delete_application(app_id):
    """Delete an application item."""
    get_table().delete_item(Key={"pk": "APPLICATION", "sk": app_id})


def update_application(app_id, updates):
    """Partial update of an application."""
    updates["updated_at"] = now_iso()
    expr_parts = []
    names = {}
    values = {}
    for i, (k, v) in enumerate(updates.items()):
        alias = f"#k{i}"
        val_alias = f":v{i}"
        expr_parts.append(f"{alias} = {val_alias}")
        names[alias] = k
        values[val_alias] = v
    resp = get_table().update_item(
        Key={"pk": "APPLICATION", "sk": app_id},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
        ReturnValues="ALL_NEW",
    )
    return resp.get("Attributes")


def list_applications(filters=None, limit=50):
    """List all applications, with optional in-memory filtering."""
    resp = get_table().query(
        KeyConditionExpression=Key("pk").eq("APPLICATION"),
    )
    items = resp["Items"]
    # Handle pagination for large result sets
    while "LastEvaluatedKey" in resp:
        resp = get_table().query(
            KeyConditionExpression=Key("pk").eq("APPLICATION"),
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp["Items"])

    if filters:
        items = _apply_filters(items, filters)

    # Sort by date descending (most recent first)
    items.sort(key=lambda x: x.get("date", ""), reverse=True)

    total = len(items)
    if limit:
        items = items[:limit]
    return {"count": total, "applications": items}


def search_applications(company_name):
    """Fuzzy search applications by company name (case-insensitive substring)."""
    result = list_applications(limit=None)
    company_lower = company_name.lower()
    matches = [
        app
        for app in result["applications"]
        if company_lower in app.get("company", "").lower()
    ]
    return {"count": len(matches), "applications": matches}


# --- Monitor Companies ---


def put_company(slug, data):
    item = {"pk": "COMPANY", "sk": slug, **data}
    get_table().put_item(Item=item)
    return item


def get_company(slug):
    resp = get_table().get_item(Key={"pk": "COMPANY", "sk": slug})
    return resp.get("Item")


def delete_company(slug):
    """Delete a monitor company."""
    get_table().delete_item(Key={"pk": "COMPANY", "sk": slug})


def update_company(slug, updates):
    expr_parts = []
    names = {}
    values = {}
    for i, (k, v) in enumerate(updates.items()):
        alias = f"#k{i}"
        val_alias = f":v{i}"
        expr_parts.append(f"{alias} = {val_alias}")
        names[alias] = k
        values[val_alias] = v
    resp = get_table().update_item(
        Key={"pk": "COMPANY", "sk": slug},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
        ReturnValues="ALL_NEW",
    )
    return resp.get("Attributes")


def list_companies(active_only=False):
    resp = get_table().query(
        KeyConditionExpression=Key("pk").eq("COMPANY"),
    )
    items = resp["Items"]
    while "LastEvaluatedKey" in resp:
        resp = get_table().query(
            KeyConditionExpression=Key("pk").eq("COMPANY"),
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp["Items"])
    if active_only:
        items = [c for c in items if c.get("active", True)]
    return items


# --- Monitor Jobs ---


def put_job(job_hash, data):
    item = {"pk": "JOB", "sk": job_hash, **data}
    get_table().put_item(Item=item)
    return item


def get_job(job_hash):
    resp = get_table().get_item(Key={"pk": "JOB", "sk": job_hash})
    return resp.get("Item")


def update_job(job_hash, updates):
    expr_parts = []
    names = {}
    values = {}
    for i, (k, v) in enumerate(updates.items()):
        alias = f"#k{i}"
        val_alias = f":v{i}"
        expr_parts.append(f"{alias} = {val_alias}")
        names[alias] = k
        values[val_alias] = v
    resp = get_table().update_item(
        Key={"pk": "JOB", "sk": job_hash},
        UpdateExpression="SET " + ", ".join(expr_parts),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
        ReturnValues="ALL_NEW",
    )
    return resp.get("Attributes")


def list_jobs(filters=None):
    resp = get_table().query(
        KeyConditionExpression=Key("pk").eq("JOB"),
    )
    items = resp["Items"]
    while "LastEvaluatedKey" in resp:
        resp = get_table().query(
            KeyConditionExpression=Key("pk").eq("JOB"),
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp["Items"])
    if filters:
        items = _apply_filters(items, filters)
    return items


# --- Scan Log ---


def put_scan_log(data):
    item = {"pk": "SCAN", "sk": now_iso(), **data}
    get_table().put_item(Item=item)
    return item


def list_scan_logs(limit=10):
    resp = get_table().query(
        KeyConditionExpression=Key("pk").eq("SCAN"),
        ScanIndexForward=False,
        Limit=limit,
    )
    return resp["Items"]


# --- Helpers ---


def _apply_filters(items, filters):
    """Apply in-memory filters to a list of items."""
    for key, value in filters.items():
        if key == "date_from":
            items = [i for i in items if i.get("date", "") >= value]
        elif key == "date_to":
            items = [i for i in items if i.get("date", "") <= value]
        elif value is not None:
            val_lower = str(value).lower()
            items = [i for i in items if val_lower in str(i.get(key, "")).lower()]
    return items


def decimal_default(obj):
    """JSON serializer for Decimal types from DynamoDB."""
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
