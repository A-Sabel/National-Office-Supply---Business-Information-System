#!/usr/bin/env python3
"""Repository DB schema & migrations scanner

Scans the repository for SQL files, migration folders (alembic/migrations),
and ORM model files (SQLAlchemy / Flask-SQLAlchemy / Django models) and
generates a JSON report and a short console summary.

Usage:
    python scripts/db_schema_scan.py --root . --out scan_report.json

"""

import argparse
import json
import re
from pathlib import Path

SQL_CREATE_RE = re.compile(r"\bCREATE\s+TABLE\b", re.IGNORECASE)
ORM_INDICATORS = [
    r"declarative_base\(",
    r"from sqlalchemy",  # generic SQLAlchemy imports
    r"Column\(",
    r"db\.Model",  # Flask-SQLAlchemy
    r"models\.Model",  # Django-ish
]


def scan(root: Path):
    report = {
        "sql_files": [],
        "migration_dirs": [],
        "orm_files": [],
        "alembic_ini": None,
        "other_candidates": [],
    }

    for p in root.rglob("*"):
        if p.is_dir():
            name = p.name.lower()
            if name in ("migrations", "alembic", "alembic_versions"):
                report["migration_dirs"].append(str(p))
            continue

        if p.suffix.lower() in (".sql", ".ddl"):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
            has_create = bool(SQL_CREATE_RE.search(text))
            entry = {"path": str(p), "contains_create_table": has_create}
            report["sql_files"].append(entry)
            continue

        if p.name.lower() == "alembic.ini":
            report["alembic_ini"] = str(p)
            continue

        if p.suffix.lower() in (".py", ".pyw"):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
            for pattern in ORM_INDICATORS:
                if re.search(pattern, text):
                    report["orm_files"].append(str(p))
                    break
            else:
                # look for raw CREATE TABLE in SQL inside python
                if SQL_CREATE_RE.search(text):
                    report["other_candidates"].append(str(p))

        # also detect raw DB schema files in directories like sqlScripts
        if (
            p.suffix.lower() in (".json", ".yml", ".yaml")
            and "schema" in p.name.lower()
        ):
            report["other_candidates"].append(str(p))

    return report


def summarize(report):
    lines = []
    lines.append(f"Migration directories found: {len(report['migration_dirs'])}")
    for d in report["migration_dirs"][:10]:
        lines.append(f"  - {d}")

    lines.append(f"SQL files found: {len(report['sql_files'])}")
    create_count = sum(1 for s in report["sql_files"] if s["contains_create_table"])
    lines.append(f"  - Files containing CREATE TABLE: {create_count}")

    lines.append(f"ORM-like Python files: {len(report['orm_files'])}")
    for f in report["orm_files"][:10]:
        lines.append(f"  - {f}")

    if report["alembic_ini"]:
        lines.append(f"Found alembic.ini at: {report['alembic_ini']}")

    lines.append(f"Other candidate files: {len(report['other_candidates'])}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Scan repo for DB schema & migrations")
    ap.add_argument("--root", default=".", help="Repo root to scan")
    ap.add_argument("--out", default="scan_report.json", help="Output JSON report file")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    print(f"Scanning: {root}")
    report = scan(root)

    out_path = Path(args.out)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Report written to:", out_path)
    print("Summary:\n")
    print(summarize(report))


if __name__ == "__main__":
    main()
