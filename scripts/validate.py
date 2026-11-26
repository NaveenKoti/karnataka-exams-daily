#!/usr/bin/env python3
"""Validate every edition. Prints a report, writes build/report.json and build/report.md.
Exit code 1 if any edition has errors (the build still publishes the valid ones)."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ked  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default=str(ROOT / "content"))
    ap.add_argument("--plan", default=str(ROOT / "data" / "plan.json"))
    ap.add_argument("--sources", default=str(ROOT / "data" / "sources.json"))
    ap.add_argument("--out", default=str(ROOT / "build"))
    a = ap.parse_args()
    plan, sources = ked.load_json(a.plan), ked.load_json(a.sources)
    results = ked.validate_all(a.content, plan, sources)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    n_err = sum(len(r["errors"]) for r in results)
    n_warn = sum(len(r["warnings"]) for r in results)
    lines = ["# Validation report", "", "Editions: %d, errors: %d, warnings: %d" % (len(results), n_err, n_warn), ""]
    for r in results:
        status = "FAIL" if r["errors"] else "ok"
        lines.append("## %s [%s]" % (r["name"], status))
        for e in r["errors"]:
            lines.append("- ERROR: " + e)
        for w in r["warnings"]:
            lines.append("- warning: " + w)
        lines.append("")
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(
        [{"name": r["name"], "errors": r["errors"], "warnings": r["warnings"]} for r in results],
        ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n".join(lines))
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
