"""Validate HTTP responses against a subset of OpenAPI 3.x contracts."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import yaml
from jsonschema import Draft202012Validator


def load_contract(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not str(data.get("openapi", "")).startswith("3."):
        raise ValueError("Expected an OpenAPI 3.x document")
    if not isinstance(data.get("paths"), dict):
        raise TypeError("OpenAPI document requires paths")
    return data


def _resolve_ref(node: object, document: dict) -> object:
    """Resolve local JSON pointers only; never fetch external references."""
    seen = set()
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/") or ref in seen:
            raise ValueError(f"Unsupported or cyclic reference: {ref}")
        seen.add(ref)
        current = document
        for part in ref[2:].split("/"):
            current = current[part.replace("~1", "/").replace("~0", "~")]
        node = current
    return node


def validate_response(document: dict, method: str, url: str, response: httpx.Response) -> list[str]:
    """Return contract violations; currently supports literal paths and JSON responses."""
    path = urlsplit(url).path or "/"
    operation = document["paths"].get(path, {}).get(method.lower())
    if not operation:
        return [f"No operation for {method.upper()} {path} (templated paths not yet supported)"]
    responses = operation.get("responses", {})
    status = str(response.status_code)
    definition = responses.get(status, responses.get("default"))
    if definition is None:
        return [f"Undocumented HTTP status {status}"]
    try:
        definition = _resolve_ref(definition, document)
        media = definition.get("content", {}).get("application/json")
        if media is None:
            return []
        schema = _resolve_ref(media.get("schema", {}), document)
        if not isinstance(schema, dict):
            return ["Invalid JSON schema in contract"]
        payload = response.json()
        # JSON Schema validates the common OpenAPI 3.1 subset. 3.0-specific
        # nullable/discriminator semantics are not yet supported.
        errors = Draft202012Validator(schema).iter_errors(payload)
        return [f"{'.'.join(map(str, err.path)) or '$'}: {err.message}" for err in sorted(errors, key=lambda e: list(map(str, e.path)))]
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return [f"Contract validation error: {exc}"]
