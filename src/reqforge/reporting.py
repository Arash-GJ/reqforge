"""Machine-readable CI reports."""

import json
from html import escape
from dataclasses import asdict
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement

from .core import Result


def save_report(results: list[Result], path: Path, fmt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        path.write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")
    elif fmt == "junit":
        root = Element(
            "testsuite", tests=str(len(results)), failures=str(sum(not r.passed for r in results))
        )
        for result in results:
            case = SubElement(
                root, "testcase", name=result.name, time=f"{result.duration_ms / 1000:.4f}"
            )
            if not result.passed:
                SubElement(case, "failure", message=result.error or "failed")
        ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    elif fmt == "html":
        passed = sum(r.passed for r in results)
        rows = "\n".join(
            "<tr><td>" + escape(r.name) + "</td><td class=\"" + ("pass" if r.passed else "fail")
            + "\">" + ("PASS" if r.passed else "FAIL") + "</td><td>"
            + escape(str(r.status if r.status is not None else "-")) + "</td><td>"
            + f"{r.duration_ms:.0f} ms" + "</td><td>"
            + escape(r.error or "") + "</td></tr>"
            for r in results
        )
        page = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
                "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                "<title>ReqForge Test Report</title><style>"
                "body{font-family:system-ui,sans-serif;max-width:1100px;margin:3rem auto;padding:0 1rem;background:#f8fafc;color:#0f172a}"
                "table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px;border-bottom:1px solid #cbd5e1;text-align:left;overflow-wrap:anywhere}"
                "th{background:#e2e8f0}.pass{color:#15803d;font-weight:700}.fail{color:#b91c1c;font-weight:700}"
                "</style></head><body><h1>ReqForge Test Report</h1><p>"
                + f"{passed}/{len(results)} passed" + "</p><table><thead><tr><th>Test</th><th>Status</th>"
                "<th>HTTP</th><th>Duration</th><th>Details</th></tr></thead><tbody>"
                + rows + "</tbody></table></body></html>")
        path.write_text(page, encoding="utf-8")
    else:
        raise ValueError("format must be json, junit or html")
