#!/usr/bin/env python3
"""
scripts/render_heatmap_svg.py

Reads data/contributions.json and writes contrib-heatmap.svg in the repository root.
Generates a GitHub-style contributions heatmap (SVG only, SMIL animations, inline CSS).

Usage: python3 scripts/render_heatmap_svg.py

This script requires only the Python standard library.
"""
import json
from datetime import datetime, timedelta
from math import ceil

IN_PATH = "data/contributions.json"
OUT_PATH = "contrib-heatmap.svg"

# GitHub contribution palette (light -> dark)
PALETTE = {
    "none": "#ebedf0",
    "low": "#9be9a8",
    "medium": "#40c463",
    "high": "#30a14e",
    "very_high": "#216e39",
}

WIDTH = 860
CELL = 12
GAP = 4
TOP_PADDING = 30
LEFT_PADDING = 20
ANIM_DUR = 0.45  # per-cell animation duration in seconds


def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_weeks(days):
    # days: list of {date: "YYYY-MM-DD", count: int, level: str}
    # Build a list of weeks (columns), each week is list of 7 entries (Sun..Sat)
    # GitHub places weeks left-to-right, each column is a week starting on Sunday.
    # Find the first date and backfill to the previous Sunday.
    dates = [datetime.strptime(d["date"], "%Y-%m-%d").date() for d in days]
    day_map = {d["date"]: d for d in days}
    first = dates[0]
    last = dates[-1]
    # backfill to Sunday
    start = first - timedelta(days=first.weekday() + 1) if first.weekday() != 6 else first
    # But Python weekday(): Monday=0..Sunday=6. We want Sunday start.
    # Adjust correctly:
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    end = last
    total_days = (end - start).days + 1
    num_weeks = ceil(total_days / 7)
    weeks = []
    cur = start
    for w in range(num_weeks):
        week = []
        for dow in range(7):
            sd = cur.strftime("%Y-%m-%d")
            entry = day_map.get(sd, {"date": sd, "count": 0, "level": "none"})
            week.append(entry)
            cur += timedelta(days=1)
        weeks.append(week)
    return weeks


def level_to_color(level):
    if level in PALETTE:
        return PALETTE[level]
    # allow synonyms
    if level in ("low", "1"):
        return PALETTE["low"]
    if level in ("medium", "2"):
        return PALETTE["medium"]
    if level in ("high", "3"):
        return PALETTE["high"]
    return PALETTE["none"]


def render_svg(weeks, generated_at, username):
    cols = len(weeks)
    svg_w = WIDTH
    svg_h = TOP_PADDING + 7 * CELL + (7 - 1) * GAP + 80  # extra for legend/footer
    # centered heatmap area: we'll compute left offset so the heatmap has exact width
    heatmap_w = cols * CELL + (cols - 1) * GAP
    offset_x = (svg_w - heatmap_w) // 2
    offset_y = TOP_PADDING

    # compute stats
    total = 0
    max_count = 0
    for week in weeks:
        for d in week:
            c = int(d.get("count", 0))
            total += c
            if c > max_count:
                max_count = c

    # build rects
    rects = []
    anim_index = 0
    for x, week in enumerate(weeks):
        for y, day in enumerate(week):
            date = day["date"]
            count = int(day.get("count", 0))
            level = day.get("level", "none")
            color = level_to_color(level)
            rx = offset_x + x * (CELL + GAP)
            ry = offset_y + y * (CELL + GAP)
            # animate from light to color
            rect = f'<rect x="{rx}" y="{ry}" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{PALETTE["none"]}" data-date="{date}" data-count="{count}">'
            # stagger begin times
            begin = f"{anim_index * 0.02}s"
            anim = (
                f'<animate attributeName="fill" from="{PALETTE["none"]}" to="{color}" dur="{ANIM_DUR}s" begin="{begin}" fill="freeze" />'
            )
            rect += anim + '</rect>'
            rects.append(rect)
            anim_index += 1

    # legend
    legend_x = offset_x
    legend_y = offset_y + 7 * (CELL + GAP) + 18
    legend_items = [("None", PALETTE["none"]), ("Low", PALETTE["low"]), ("Medium", PALETTE["medium"]), ("High", PALETTE["high"]), ("Very high", PALETTE["very_high"])]
    legend_html = []
    lx = legend_x
    for name, col in legend_items:
        legend_html.append(f'<rect x="{lx}" y="{legend_y}" width="12" height="12" rx="2" ry="2" fill="{col}" />')
        legend_html.append(f'<text x="{lx + 18}" y="{legend_y + 11}" font-family="Inter,Segoe UI,Helvetica,Arial,sans-serif" font-size="12" fill="#c9d1d9">{name}</text>')
        lx += 120

    footer_y = legend_y + 28
    footer = f'<text x="{svg_w//2}" y="{footer_y}" font-family="Inter,Segoe UI,Helvetica,Arial,sans-serif" font-size="13" fill="#8b949e" text-anchor="middle">{username} · total contributions: {total} · generated: {generated_at}</text>'

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}px" height="{svg_h}px" viewBox="0 0 {svg_w} {svg_h}" role="img" aria-label="Contribution heatmap for {username}">',
        '<style>',
        '  text { font-family: Inter,Segoe UI,Helvetica,Arial,sans-serif; }',
        '</style>',
        f'<rect width="100%" height="100%" fill="#0d1117" />',
        # Title
        f'<text x="{svg_w//2}" y="18" font-size="16" fill="#c9d1d9" text-anchor="middle">Contributions</text>',
        # grid
        '<g id="heatmap">',
        *rects,
        '</g>',
        # legend
        '<g id="legend">',
        *legend_html,
        '</g>',
        footer,
        '</svg>'
    ]
    return "\n".join(svg)


def main():
    data = load_data(IN_PATH)
    username = data.get("username", "user")
    generated_at = data.get("generated_at", datetime.utcnow().isoformat() + "Z")
    days = data.get("days", [])
    if not days:
        print("No contribution days found in", IN_PATH)
        return
    weeks = build_weeks(days)
    svg = render_svg(weeks, generated_at, username)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print("Wrote", OUT_PATH)


if __name__ == "__main__":
    main()
