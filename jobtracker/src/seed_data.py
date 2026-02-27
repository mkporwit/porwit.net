"""Seed data for monitor companies — sourced from Monitor_Companies.xlsx."""

MONITOR_COMPANIES = [
    # ── HEALTHCARE / HEALTHTECH ──
    {"slug": "includedhealth", "name": "Included Health", "sector": "Healthcare", "ats": "lever", "careers_url": "https://jobs.lever.co/includedhealth", "active": True},
    {"slug": "hingehealth", "name": "Hinge Health", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/hingehealth", "active": True},
    {"slug": "thirtymadison", "name": "Thirty Madison", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/thirtymadison", "active": True},
    {"slug": "cityblockhealth", "name": "Cityblock Health", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/cityblockhealth", "active": True},
    {"slug": "aledade", "name": "Aledade", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/aledade", "active": True},
    {"slug": "devotedhealth", "name": "Devoted Health", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/devotedhealth", "active": True},
    {"slug": "noom", "name": "Noom", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/noom", "active": True},
    {"slug": "springhealth", "name": "Spring Health", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/springhealth", "active": True},
    {"slug": "virtahealth", "name": "Virta Health", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/virtahealth", "active": True},
    {"slug": "capsule", "name": "Capsule", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/capsule", "active": True},
    {"slug": "parachutehealth", "name": "Parachute Health", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/parachutehealth", "active": True},
    {"slug": "rula", "name": "Rula (Path)", "sector": "Healthcare", "ats": "ashby", "careers_url": "https://jobs.ashbyhq.com/rula", "active": True},
    {"slug": "rezilienthealth", "name": "Rezilient Health", "sector": "Healthcare", "ats": "workable", "careers_url": "https://apply.workable.com/rezilient", "active": True},
    {"slug": "coherehealth", "name": "Cohere Health", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/coherehealth", "active": True},
    {"slug": "genomenon", "name": "Genomenon", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/genomenon", "active": True},
    {"slug": "imaginepediatrics", "name": "Imagine Pediatrics", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/imaginepediatrics", "active": True},
    {"slug": "smarterdx", "name": "SmarterDx", "sector": "Healthcare", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/smarterdx", "active": True},
    {"slug": "paradigmhealth", "name": "Paradigm Health", "sector": "Healthcare", "ats": "custom", "careers_url": "https://www.linkedin.com/jobs/view/4356832032/", "active": False},

    # ── DEVELOPER TOOLS / INFRA ──
    {"slug": "temporal", "name": "Temporal", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/temporaltechnologies", "active": True},
    {"slug": "grafana", "name": "Grafana Labs", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/grafanalabs", "active": True},
    {"slug": "launchdarkly", "name": "LaunchDarkly", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/launchdarkly", "active": True},
    {"slug": "pulumi", "name": "Pulumi", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/pulumi", "active": True},
    {"slug": "vercel", "name": "Vercel", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/vercel", "active": True},
    {"slug": "supabase", "name": "Supabase", "sector": "Dev Tools", "ats": "ashby", "careers_url": "https://jobs.ashbyhq.com/supabase", "active": True},
    {"slug": "flyio", "name": "Fly.io", "sector": "Dev Tools", "ats": "custom", "careers_url": "https://fly.io/jobs", "active": False},
    {"slug": "redpanda", "name": "Redpanda Data", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/redpandadata", "active": True},
    {"slug": "docker", "name": "Docker", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/docker", "active": True},
    {"slug": "webflow", "name": "Webflow", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/webflow", "active": True},
    {"slug": "hashicorp", "name": "HashiCorp", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/hashicorp", "active": True},
    {"slug": "honeycomb", "name": "Honeycomb", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/honeycomb", "active": True},
    {"slug": "figma", "name": "Figma", "sector": "Dev Tools", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/figma", "active": True},

    # ── FINTECH ──
    {"slug": "brex", "name": "Brex", "sector": "Fintech", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/brex", "active": True},
    {"slug": "ramp", "name": "Ramp", "sector": "Fintech", "ats": "ashby", "careers_url": "https://jobs.ashbyhq.com/ramp", "active": True},
    {"slug": "mercury", "name": "Mercury", "sector": "Fintech", "ats": "ashby", "careers_url": "https://jobs.ashbyhq.com/mercury", "active": True},
    {"slug": "plaid", "name": "Plaid", "sector": "Fintech", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/plaid", "active": True},
    {"slug": "sardine", "name": "Sardine", "sector": "Fintech", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/sardine", "active": True},
    {"slug": "affirm", "name": "Affirm", "sector": "Fintech", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/affirm", "active": True},

    # ── DEFENSE TECH ──
    {"slug": "anduril", "name": "Anduril", "sector": "Defense Tech", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/andurilindustries", "active": True},
    {"slug": "shieldai", "name": "Shield AI", "sector": "Defense Tech", "ats": "lever", "careers_url": "https://jobs.lever.co/shieldai", "active": True},
    {"slug": "hadrian", "name": "Hadrian", "sector": "Defense Tech", "ats": "ashby", "careers_url": "https://jobs.ashbyhq.com/hadrian-automation", "active": True},
    {"slug": "epirus", "name": "Epirus", "sector": "Defense Tech", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/epirus", "active": True},
    {"slug": "skydio", "name": "Skydio", "sector": "Defense Tech", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/skydio", "active": True},

    # ── SPACE TECH ──
    {"slug": "planetlabs", "name": "Planet Labs", "sector": "Space Tech", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/planetlabs", "active": True},
    {"slug": "relativityspace", "name": "Relativity Space", "sector": "Space Tech", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/relativity", "active": True},
    {"slug": "rocketlab", "name": "Rocket Lab", "sector": "Space Tech", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/rocketlab", "active": True},
    {"slug": "vardaspace", "name": "Varda Space", "sector": "Space Tech", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/vardaspace", "active": True},
    {"slug": "muonspace", "name": "Muon Space", "sector": "Space Tech", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/muonspace", "active": True},

    # ── CLIMATE TECH ──
    {"slug": "arcadia", "name": "Arcadia", "sector": "Climate Tech", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/arcadiacareers", "active": True},
    {"slug": "watershed", "name": "Watershed", "sector": "Climate Tech", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/watershedclimate", "active": True},
    {"slug": "palmetto", "name": "Palmetto", "sector": "Climate Tech", "ats": "greenhouse", "careers_url": "https://job-boards.greenhouse.io/palmettocleantech", "active": True},

    # ── MARKETPLACE / PLATFORM ──
    {"slug": "faire", "name": "Faire", "sector": "Marketplace", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/faire", "active": True},
    {"slug": "flexport", "name": "Flexport", "sector": "Marketplace", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/flexport", "active": True},
    {"slug": "samsara", "name": "Samsara", "sector": "IoT / Platform", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/samsara", "active": True},
    {"slug": "rippling", "name": "Rippling", "sector": "HR Platform", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/rippling", "active": True},

    # ── INTERVIEW TRACTION / REVISIT ──
    {"slug": "okta", "name": "Okta (Auth0)", "sector": "Security", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/okta", "active": True},
    {"slug": "amperity", "name": "Amperity", "sector": "Data Platform", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/amperity", "active": True},
    {"slug": "vanta", "name": "Vanta", "sector": "Security", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/vanta", "active": True},
    {"slug": "ltk", "name": "LTK", "sector": "Creator Economy", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/ltk", "active": True},
    {"slug": "dropbox", "name": "Dropbox", "sector": "Productivity", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/dropbox", "active": True},
    {"slug": "stitchfix", "name": "Stitch Fix", "sector": "E-commerce", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/stitchfix", "active": True},
    {"slug": "mixpanel", "name": "MixPanel", "sector": "Analytics", "ats": "greenhouse", "careers_url": "https://boards.greenhouse.io/mixpanel", "active": True},
    {"slug": "aurora", "name": "Aurora Innovation", "sector": "Autonomous", "ats": "custom", "careers_url": "https://aurora.tech/careers", "active": False},

    # ── WORKDAY ATS ──
    {"slug": "crowdstrike", "name": "CrowdStrike", "sector": "Security", "ats": "workday", "careers_url": "https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers", "active": True},
    {"slug": "nordstrom", "name": "Nordstrom", "sector": "Retail Tech", "ats": "workday", "careers_url": "https://nordstrom.wd501.myworkdayjobs.com/nordstrom_careers", "active": True},
    {"slug": "dexcom", "name": "DexCom", "sector": "Healthcare/Devices", "ats": "workday", "careers_url": "", "active": False},
    {"slug": "alcon", "name": "Alcon", "sector": "Healthcare/Devices", "ats": "workday", "careers_url": "", "active": False},
    {"slug": "gehealthcare", "name": "GE Healthcare", "sector": "Healthcare/Devices", "ats": "workday", "careers_url": "", "active": False},
]


def seed_companies():
    """Insert all monitor companies into DynamoDB."""
    import db
    for company in MONITOR_COMPANIES:
        slug = company.pop("slug")
        db.put_company(slug, company)
        company["slug"] = slug  # restore for re-use
    print(f"Seeded {len(MONITOR_COMPANIES)} companies")


if __name__ == "__main__":
    seed_companies()
