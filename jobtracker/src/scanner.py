"""Career page scanner Lambda handler.

Fetches job listings from target companies and identifies
engineering leadership roles.
"""

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

import db

# --- Title Matching ---

INCLUDE_PATTERNS = [
    r"director.*engineer", r"director.*platform", r"director.*infra",
    r"director.*cloud", r"director.*sre", r"director.*devops",
    r"director.*software", r"vp.*engineer", r"vice.president.*engineer",
    r"head.*engineer", r"sr\.?\s*director.*engineer", r"senior\s+director.*engineer",
    r"senior.*engineering\s+manager", r"sr\.?\s*engineering\s+manager",
    r"engineering\s+manager.*platform", r"engineering\s+manager.*cloud",
    r"engineering\s+manager.*infra", r"engineering\s+manager.*sre",
]

EXCLUDE_PATTERNS = [
    r"sales\s+engineer", r"solutions\s+engineer", r"civil", r"mechanical",
    r"electrical", r"field", r"customer", r"quality", r"manufacturing", r"hardware",
]

GOOD_LOCATIONS = [
    "remote", "united states", "seattle", "bellevue", "austin", "dallas",
    "fort worth", "san antonio", "nashville", "knoxville", "salt lake", "boise",
]

BAD_LOCATIONS = [
    "pittsburgh", "new york on-site", "san francisco on-site", "bay area on-site",
]


def matches_title(title):
    """Check if a job title matches engineering leadership patterns."""
    t = title.lower()
    if any(re.search(p, t) for p in EXCLUDE_PATTERNS):
        return False
    return any(re.search(p, t) for p in INCLUDE_PATTERNS)


def location_flag(location):
    """Classify location as good/bad/unknown."""
    loc = (location or "").lower()
    if any(g in loc for g in GOOD_LOCATIONS):
        return "good"
    if any(b in loc for b in BAD_LOCATIONS):
        return "bad"
    return "unknown"


def job_hash(company, title, url):
    """Generate a unique hash for a job posting."""
    raw = f"{company}{title}{url}"
    return hashlib.md5(raw.encode()).hexdigest()


# --- Parsers ---


def parse_greenhouse(company_name, sector, careers_url):
    """Parse Greenhouse job board HTML."""
    jobs = []
    try:
        resp = requests.get(careers_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for link in soup.find_all("a", href=re.compile(r"/jobs/")):
            # Extract title from the first <p> (body--medium) or the link text
            title_el = link.find("p", class_=re.compile(r"body--medium"))
            if title_el:
                title = title_el.get_text(strip=True)
            else:
                title = link.get_text(strip=True)

            if not title or not matches_title(title):
                continue

            href = link.get("href", "")
            if not href.startswith("http"):
                from urllib.parse import urljoin
                href = urljoin(careers_url, href)

            # Extract location from metadata <p> or nearby elements
            loc = ""
            loc_el = link.find("p", class_=re.compile(r"metadata"))
            if loc_el:
                loc = loc_el.get_text(strip=True)
            else:
                loc = _extract_greenhouse_location(link)

            jobs.append({
                "company": company_name,
                "sector": sector,
                "title": title,
                "location": loc,
                "url": href,
            })
    except Exception as e:
        return jobs, str(e)
    return jobs, None


def _extract_greenhouse_location(link_element):
    """Fallback: try to extract location from Greenhouse HTML near a job link."""
    parent = link_element.parent
    if parent:
        location_span = parent.find("span", class_=re.compile(r"location", re.I))
        if location_span:
            return location_span.get_text(strip=True)
        for sibling in parent.find_all("span"):
            text = sibling.get_text(strip=True)
            if text and text != link_element.get_text(strip=True):
                return text
    return ""


def parse_lever(company_name, sector, careers_url):
    """Parse Lever job board HTML."""
    jobs = []
    try:
        resp = requests.get(careers_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for posting in soup.find_all("a", class_="posting-title"):
            title_el = posting.find("h5")
            title = title_el.get_text(strip=True) if title_el else posting.get_text(strip=True)
            if not matches_title(title):
                continue
            href = posting.get("href", "")
            loc_el = posting.find_next("span", class_="sort-by-location")
            loc = loc_el.get_text(strip=True) if loc_el else ""
            jobs.append({
                "company": company_name,
                "sector": sector,
                "title": title,
                "location": loc,
                "url": href,
            })
    except Exception as e:
        return jobs, str(e)
    return jobs, None


def parse_ashby(company_name, sector, careers_url):
    """Parse Ashby job board JSON API."""
    jobs = []
    try:
        # Extract org slug from URL
        slug = careers_url.rstrip("/").split("/")[-1]
        api_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
        resp = requests.get(api_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        for job in data.get("jobs", []):
            title = job.get("title", "")
            if not matches_title(title):
                continue
            loc = job.get("location", {})
            if isinstance(loc, dict):
                loc = loc.get("name", "")
            job_id = job.get("id", "")
            url = f"https://jobs.ashbyhq.com/{slug}/{job_id}"
            jobs.append({
                "company": company_name,
                "sector": sector,
                "title": title,
                "location": loc,
                "url": url,
            })
    except Exception as e:
        return jobs, str(e)
    return jobs, None


def parse_workable(company_name, sector, careers_url):
    """Parse Workable job board JSON API."""
    jobs = []
    try:
        slug = careers_url.rstrip("/").split("/")[-1]
        api_url = f"https://apply.workable.com/api/v3/accounts/{slug}/jobs"
        resp = requests.post(
            api_url,
            json={"query": "", "location": []},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        for result in data.get("results", []):
            title = result.get("title", "")
            if not matches_title(title):
                continue
            loc = result.get("location", {})
            if isinstance(loc, dict):
                parts = [loc.get("city", ""), loc.get("region", ""), loc.get("country", "")]
                loc = ", ".join(p for p in parts if p)
            shortcode = result.get("shortcode", "")
            url = f"https://apply.workable.com/{slug}/j/{shortcode}/"
            jobs.append({
                "company": company_name,
                "sector": sector,
                "title": title,
                "location": loc if isinstance(loc, str) else "",
                "url": url,
            })
    except Exception as e:
        return jobs, str(e)
    return jobs, None


def parse_pinpoint(company_name, sector, careers_url):
    """Parse Pinpoint HQ job board JSON API."""
    jobs = []
    try:
        slug = careers_url.rstrip("/").split("/")[2].split(".")[0]  # e.g. "impulsespace" from "https://impulsespace.pinpointhq.com/"
        api_url = f"https://{slug}.pinpointhq.com/postings.json"
        resp = requests.get(api_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        for posting in data.get("data", []):
            title = posting.get("title", "")
            if not matches_title(title):
                continue
            loc = posting.get("location", {})
            if isinstance(loc, dict):
                parts = [loc.get("city", ""), loc.get("province", "")]
                loc = ", ".join(p for p in parts if p)
            url = posting.get("url", "")
            jobs.append({
                "company": company_name,
                "sector": sector,
                "title": title,
                "location": loc if isinstance(loc, str) else "",
                "url": url,
            })
    except Exception as e:
        return jobs, str(e)
    return jobs, None


def parse_workday(company_name, sector, careers_url):
    """Parse Workday job board JSON API.

    careers_url format: https://{company}.{wd}.myworkdayjobs.com/en-US/{board}
    e.g. https://shieldai.wd5.myworkdayjobs.com/en-US/Shield_AI_Career_Site
    """
    jobs = []
    try:
        # Parse URL components: company, wd instance, board name
        from urllib.parse import urlparse
        parsed = urlparse(careers_url)
        host = parsed.hostname  # e.g. shieldai.wd5.myworkdayjobs.com
        parts = host.split(".")
        company_slug = parts[0]  # e.g. shieldai
        # Board is the last path segment
        board = parsed.path.rstrip("/").split("/")[-1]  # e.g. Shield_AI_Career_Site

        api_url = f"https://{host}/wday/cxs/{company_slug}/{board}/jobs"

        # Workday uses Cloudflare; a session with cookies from an initial request is needed
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

        offset = 0
        limit = 20

        while True:
            resp = session.post(
                api_url,
                json={"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": ""},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()

            total = data.get("total", 0)
            postings = data.get("jobPostings", [])

            for posting in postings:
                title = posting.get("title", "")
                if not matches_title(title):
                    continue
                loc = posting.get("locationsText", "")
                ext_path = posting.get("externalPath", "")
                url = f"https://{host}{ext_path}" if ext_path else ""
                jobs.append({
                    "company": company_name,
                    "sector": sector,
                    "title": title,
                    "location": loc,
                    "url": url,
                })

            offset += limit
            if offset >= total or not postings:
                break

    except Exception as e:
        return jobs, str(e)
    return jobs, None


PARSERS = {
    "greenhouse": parse_greenhouse,
    "lever": parse_lever,
    "ashby": parse_ashby,
    "workable": parse_workable,
    "pinpoint": parse_pinpoint,
    "workday": parse_workday,
}


# --- Scanner Logic ---


def run_scan():
    """Run a full scan of all active monitor companies."""
    start = time.time()
    companies = db.list_companies(active_only=True)

    all_found_hashes = set()
    total_matches = 0
    new_matches = 0
    errors = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for company in companies:
        ats = company.get("ats", "")
        parser = PARSERS.get(ats)
        if not parser:
            errors.append({"company": company["name"], "error": f"Unknown ATS: {ats}"})
            continue

        found_jobs, error = parser(
            company["name"],
            company.get("sector", ""),
            company.get("careers_url", ""),
        )
        if error:
            errors.append({"company": company["name"], "error": error})

        for job in found_jobs:
            h = job_hash(job["company"], job["title"], job["url"])
            all_found_hashes.add(h)
            total_matches += 1

            existing = db.get_job(h)
            if existing:
                db.update_job(h, {"last_seen": today})
            else:
                new_matches += 1
                db.put_job(h, {
                    "company": job["company"],
                    "sector": job["sector"],
                    "title": job["title"],
                    "location": job["location"],
                    "location_flag": location_flag(job["location"]),
                    "url": job["url"],
                    "first_seen": today,
                    "last_seen": today,
                    "gone": False,
                    "status": "new",
                })

    # Mark jobs as gone if not seen in this scan
    all_jobs = db.list_jobs()
    for job in all_jobs:
        if not job.get("gone", False) and job["sk"] not in all_found_hashes:
            db.update_job(job["sk"], {"gone": True, "status": "gone"})

    duration = time.time() - start

    # Log the scan
    db.put_scan_log({
        "companies_checked": len(companies),
        "total_matches": total_matches,
        "new_matches": new_matches,
        "errors": json.dumps(errors),
        "duration_seconds": Decimal(str(round(duration, 2))),
    })

    return {
        "companies_checked": len(companies),
        "total_matches": total_matches,
        "new_matches": new_matches,
        "errors": errors,
        "duration_seconds": round(duration, 2),
    }


def lambda_handler(event, context):
    """Lambda entry point for scheduled or manual scans."""
    result = run_scan()
    print(f"Scan complete: {json.dumps(result)}")
    return result
