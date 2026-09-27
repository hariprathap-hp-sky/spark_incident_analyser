"""
Seed Postgres with sample incidents from data/incidents/*.txt.

Handles TWO file formats found in that folder:

1. Synthetic format (INC-2024-XXX.txt):
     Incident ID: ...
     Date: ...
     Cluster: ...
     Application: ...
     Error Summary: ...
     Work Notes:
     <free text>

2. Real ServiceNow export format (INCxxxxxxx.txt):
     number: ...
     incident_state: Closed
     short_description: ...
     description: ...
     comments: ...
     work_notes: ...
     (no cluster/application/date fields — these are ISP/telecom tickets,
      not Spark-specific)

This lets you test the REAL ingestion path (app/ingestion/pipeline.py)
end-to-end instead of upserting directly into Qdrant.

Usage:
    python -m scripts.seed_incidents
"""

from __future__ import annotations

import re
from pathlib import Path

import psycopg2

from app.config import cfg

INCIDENTS_DIR = Path(__file__).parent.parent / "data" / "incidents"


def _parse_kv_lines(text: str) -> dict:
    """Generic 'key: value' per-line parser used by both formats."""
    fields: dict[str, str] = {}
    current_key = None
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z][A-Za-z0-9_ ]*?):\s?(.*)$", line)
        if m and m.group(1).strip():
            current_key = m.group(1).strip().lower().replace(" ", "_")
            fields[current_key] = m.group(2).strip()
        elif current_key:
            # continuation line (e.g. synthetic format's multi-line Work Notes)
            fields[current_key] += ("\n" + line if fields[current_key] else line)
    return fields


def _parse_file(path: Path) -> dict:
    text = path.read_text(errors="ignore")
    raw = _parse_kv_lines(text)

    if "incident_id" in raw:
        # Synthetic format
        return {
            "incident_id": raw.get("incident_id", "").strip(),
            "created_date": raw.get("date", "").strip() or None,
            "cluster": raw.get("cluster", "").strip(),
            "application": raw.get("application", "").strip(),
            "description": raw.get("error_summary", "").strip(),
            "work_notes": raw.get("work_notes", "").strip(),
            "status": "RESOLVED",
        }

    # Real ServiceNow export format
    state = raw.get("incident_state", "").strip().lower()
    status = "RESOLVED" if state in ("closed", "resolved") else state.upper() or "RESOLVED"

    description = "\n\n".join(
        p for p in [raw.get("short_description", ""), raw.get("description", "")] if p
    )
    work_notes = "\n\n".join(
        p for p in [raw.get("comments", ""), raw.get("work_notes", "")] if p
    )

    # No explicit date field in this export — pull the earliest dd/mm/yyyy
    # timestamp found in work_notes/comments as a best-effort created_date.
    date_match = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", work_notes)
    created_date = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}" if date_match else None

    return {
        "incident_id": raw.get("number", "").strip(),
        "created_date": created_date,
        "cluster": "",       # not present in this export — pipeline handles blanks fine
        "application": "",   # not present in this export
        "description": description,
        "work_notes": work_notes,
        "status": status,
    }


def main() -> None:
    files = sorted(INCIDENTS_DIR.glob("*.txt"))
    print(f"Found {len(files)} incident files in {INCIDENTS_DIR}")

    rows = [_parse_file(f) for f in files]
    skipped = [r for r in rows if not r["incident_id"]]
    rows = [r for r in rows if r["incident_id"]]
    if skipped:
        print(f"Skipped {len(skipped)} file(s) with no parseable incident_id")

    db = cfg.database
    conn = psycopg2.connect(
        host=db.host, port=db.port, dbname=db.name, user=db.user, password=db.password
    )
    try:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    """
                    INSERT INTO incidents
                        (incident_id, created_date, cluster, application,
                         description, work_notes, status, ingested)
                    VALUES (%s, COALESCE(%s::timestamptz, NOW()), %s, %s, %s, %s, %s, FALSE)
                    ON CONFLICT (incident_id) DO NOTHING
                    """,
                    (
                        row["incident_id"],
                        row["created_date"],
                        row["cluster"],
                        row["application"],
                        row["description"],
                        row["work_notes"],
                        row["status"],
                    ),
                )
        conn.commit()
        print(f"Seeded {len(rows)} incidents (duplicates skipped).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()