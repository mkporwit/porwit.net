#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///
"""Generate openapi.yaml from the route registry (single source of truth)."""

import sys
import os
from collections import OrderedDict
from pathlib import Path

# Add src/ to path so we can import routes and schemas
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import routes
import schemas

import yaml


# Custom YAML representer to preserve dict ordering and emit multiline strings
class OrderedDumper(yaml.SafeDumper):
    pass


def _dict_representer(dumper, data):
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


def _str_representer(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def _bool_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:bool", "true" if data else "false")


OrderedDumper.add_representer(OrderedDict, _dict_representer)
OrderedDumper.add_representer(dict, _dict_representer)
OrderedDumper.add_representer(str, _str_representer)
OrderedDumper.add_representer(bool, _bool_representer)


def build_spec():
    """Build the OpenAPI 3.0.3 spec dict from routes and schemas."""
    paths = OrderedDict()

    for route in routes.ROUTES:
        path = route.path
        method = route.method.lower()

        if path not in paths:
            paths[path] = OrderedDict()

        operation = OrderedDict()
        operation["summary"] = route.summary

        if route.description:
            operation["description"] = route.description

        # No auth → override global security
        if not route.auth:
            operation["security"] = []

        if route.parameters:
            operation["parameters"] = route.parameters

        if route.request_body:
            operation["requestBody"] = route.request_body

        operation["responses"] = OrderedDict()
        for status_code in sorted(route.responses.keys()):
            operation["responses"][status_code] = route.responses[status_code]

        paths[path][method] = operation

    spec = OrderedDict([
        ("openapi", "3.0.3"),
        ("info", OrderedDict([
            ("title", "JobTracker API"),
            ("description",
             "Job application tracker and career page monitor.\n"
             "Tracks job applications, monitors company career pages for matching roles,\n"
             "and provides analytics on the job search pipeline.\n"),
            ("version", "1.0.0"),
        ])),
        ("servers", [
            OrderedDict([
                ("url", "https://jobtracker.porwit.net/api"),
                ("description", "Production"),
            ]),
        ]),
        ("security", [{"BearerAuth": []}]),
        ("paths", paths),
        ("components", OrderedDict([
            ("securitySchemes", schemas.SECURITY_SCHEMES),
            ("schemas", schemas.SCHEMAS),
            ("responses", OrderedDict([
                ("Error", schemas.ERROR_RESPONSE),
            ])),
        ])),
    ])

    return spec


def main():
    spec = build_spec()
    out_path = Path(__file__).resolve().parent.parent / "openapi.yaml"

    yaml_str = yaml.dump(
        spec,
        Dumper=OrderedDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )

    out_path.write_text(yaml_str)
    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
