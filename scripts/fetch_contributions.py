#!/usr/bin/env python3
"""Fetch and parse the public GitHub contribution calendar from the HTML endpoint."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = ROOT / "data" / "contributions.json"
USERNAME = "virajpotdar"
CONTRIBUTIONS_URL = f"https://github.com/users/{USERNAME}/contributions"

# GitHub contribution levels as they appear in the contribution graph SVG.
LEVELS = {
    "0": "none",
    "1": "low",
    "2": "medium",
    "3": "high",
    "4": "max",
}


def fetch_contributions_html(url: str) -> str:
    """Fetch the public contribution page and raise a clear error on failure."""
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Unable to download contribution page: {exc}") from exc

    html = response.text
    if not html or "contribution-graph" not in html and "calendar" not in html:
        raise RuntimeError("Contribution page did not contain expected GitHub calendar markup")
    return html


def parse_contribution_days(html: str) -> list[dict[str, Any]]:
    """Parse daily contribution data from GitHub's current contribution calendar markup."""
    soup = BeautifulSoup(html, "html.parser")

    # GitHub renders the contribution calendar as table cells with data-date and data-level.
    candidate_cells = soup.select("td[data-date]")
    if not candidate_cells:
        raise RuntimeError("No contribution cells were found in the HTML")

    entries: list[dict[str, Any]] = []
    for cell in candidate_cells:
        raw_date = cell.get("data-date")
        if not raw_date:
            continue

        try:
            date_value = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            continue

        # GitHub exposes the contribution level, but the daily count is not always present in the HTML.
        # We therefore use the level as a proxy and default to zero when the count is unavailable.
        raw_level = cell.get("data-level")
        level = LEVELS.get(str(raw_level), "none") if raw_level is not None else "none"

        count = 0
        if level == "none":
            count = 0
        elif level == "low":
            count = 1
        elif level == "medium":
            count = 3
        elif level == "high":
            count = 5
        elif level == "max":
            count = 8

        entries.append(
            {
                "date": date_value.isoformat(),
                "count": count,
                "level": level,
            }
        )

    entries.sort(key=lambda item: item["date"])
    return entries


def compute_statistics(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute summary statistics from the parsed contribution history."""
    if not entries:
        return {
            "total_contributions": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "best_day": None,
            "monthly_totals": {},
            "active_days": 0,
            "average_contributions_per_active_day": 0.0,
            "average_contributions_per_calendar_day": 0.0,
        }

    counts = [entry["count"] for entry in entries]
    total_contributions = sum(counts)

    # Current streak counts consecutive days ending with the latest available date.
    current_streak = 0
    for entry in reversed(entries):
        if entry["count"] > 0:
            current_streak += 1
        else:
            break

    # Longest streak counts consecutive non-zero contribution days.
    longest_streak = 0
    streak = 0
    for entry in entries:
        if entry["count"] > 0:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    best_entry = max(entries, key=lambda item: (item["count"], item["date"]))
    best_day = {
        "date": best_entry["date"],
        "count": best_entry["count"],
        "level": best_entry["level"],
    }

    monthly_totals: Counter[str] = Counter()
    for entry in entries:
        month_key = entry["date"][:7]
        monthly_totals[month_key] += entry["count"]

    active_days = sum(1 for entry in entries if entry["count"] > 0)
    average_contributions_per_active_day = round(total_contributions / active_days, 2) if active_days else 0.0
    average_contributions_per_calendar_day = round(total_contributions / len(entries), 2) if entries else 0.0

    return {
        "total_contributions": total_contributions,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": dict(sorted(monthly_totals.items())),
        "active_days": active_days,
        "average_contributions_per_active_day": average_contributions_per_active_day,
        "average_contributions_per_calendar_day": average_contributions_per_calendar_day,
    }


def build_payload(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Assemble the final JSON payload for use by the SVG renderer."""
    stats = compute_statistics(entries)
    return {
        "username": USERNAME,
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "days": entries,
        "summary": stats,
    }


def main() -> None:
    """Download, parse, and save the contribution history."""
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    try:
        html = fetch_contributions_html(CONTRIBUTIONS_URL)
        entries = parse_contribution_days(html)
        payload = build_payload(entries)
        OUTPUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except RuntimeError as exc:
        # Persist a graceful fallback payload when the network or HTML is unavailable.
        fallback_payload = {
            "username": USERNAME,
            "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "days": [],
            "summary": {
                "total_contributions": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "best_day": None,
                "monthly_totals": {},
                "active_days": 0,
                "average_contributions_per_active_day": 0.0,
                "average_contributions_per_calendar_day": 0.0,
            },
            "error": str(exc),
        }
        OUTPUT_JSON.write_text(json.dumps(fallback_payload, indent=2), encoding="utf-8")
        print(f"Warning: {exc}")

    data = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    print(
        f"Saved {OUTPUT_JSON} | total={summary.get('total_contributions', 0)} "
        f"streak={summary.get('current_streak', 0)} longest={summary.get('longest_streak', 0)} "
        f"days={len(data.get('days', []))}"
    )


if __name__ == "__main__":
    main()
