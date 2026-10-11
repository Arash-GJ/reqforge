"""Machine-readable CI reports."""
import json
from dataclasses import asdict
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree
from .core import Result


def save_report(results: list[Result], path: Path, fmt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        path.write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")
    elif fmt == "junit":
        root = Element("testsuite", tests=str(len(results)), failures=str(sum(not r.passed for r in results)))
        for result in results:
            case = SubElement(root, "testcase", name=result.name, time=f"{result.duration_ms / 1000:.4f}")
            if not result.passed:
                SubElement(case, "failure", message=result.error or "failed")
        ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    else:
        raise ValueError("format must be json or junit")
