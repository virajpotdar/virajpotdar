#!/usr/bin/env python3
"""Generate a terminal-style animated SVG profile info card."""
from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_SVG = ROOT / "info-card.svg"

# Editable profile details.
NAME = "Viraj Potdar"
ROLE = "Software Engineer"
LOCATION = "Pune, India"
CURRENT_FOCUS = "Python • Automation • Developer Tools"
PREVIOUS_EXPERIENCE = "Backend services, data pipelines, web apps"
TECH_STACK = "Python, FastAPI, Flask, Docker, GitHub Actions"
HIGHLIGHTS = "Open-source contributor • CI/CD • Clean architecture"
GITHUB_USERNAME = "virajpotdar"
WEBSITE = "https://github.com/virajpotdar"

# Visual styling.
WIDTH = 760
HEIGHT = 460
PADDING_X = 32
PADDING_Y = 28
LINE_HEIGHT = 34
TEXT_X = 44
START_Y = 92

# Animation settings.
STATIC = os.getenv("STATIC", "0") == "1"
ROW_DELAY_BASE = 0.08
ROW_DELAY_STEP = 0.09
FADE_DURATION = 0.55
SLIDE_DISTANCE = 8


def build_rows() -> list[tuple[str, str]]:
    """Return the visible rows to render in the card."""
    return [
        ("Name", NAME),
        ("Role", ROLE),
        ("Location", LOCATION),
        ("Current Focus", CURRENT_FOCUS),
        ("Previous Experience", PREVIOUS_EXPERIENCE),
        ("Tech Stack", TECH_STACK),
        ("Highlights", HIGHLIGHTS),
        ("GitHub", GITHUB_USERNAME),
        ("Website", WEBSITE),
    ]


def build_svg() -> str:
    """Build the final self-contained SVG markup."""
    rows = build_rows()
    body_parts: list[str] = []

    # Header bar and title.
    body_parts.append(
        '<rect x="0" y="0" width="100%" height="100%" rx="24" ry="24" fill="#0d1117" />'
    )
    body_parts.append(
        '<rect x="0" y="0" width="100%" height="54" rx="24" ry="24" fill="#161b22" />'
    )
    body_parts.append(
        '<circle cx="28" cy="27" r="7" fill="#ff5f56" />'
    )
    body_parts.append(
        '<circle cx="50" cy="27" r="7" fill="#febc2e" />'
    )
    body_parts.append(
        '<circle cx="72" cy="27" r="7" fill="#2ecc71" />'
    )
    body_parts.append(
        '<text x="116" y="31" fill="#8b949e" font-family="Consolas, monospace" font-size="16">terminal profile</text>'
    )

    # Decorative top line and status text.
    body_parts.append(
        '<rect x="32" y="74" width="696" height="1" fill="#30363d" />'
    )
    body_parts.append(
        '<text x="44" y="60" fill="#58a6ff" font-family="Consolas, monospace" font-size="15">~/profile</text>'
    )

    # Build each row with animation wrappers.
    for index, (label, value) in enumerate(rows):
        y = START_Y + index * LINE_HEIGHT
        delay = index * ROW_DELAY_STEP
        label_text = f'<text x="{TEXT_X}" y="{y}" fill="#8b949e" font-family="Consolas, monospace" font-size="16">{escape(label)}:</text>'
        value_text = (
            f'<text x="{TEXT_X + 140}" y="{y}" fill="#f0f6fc" font-family="Consolas, monospace" font-size="16">{escape(value)}</text>'
        )

        if STATIC:
            body_parts.append(f'<g>{label_text}{value_text}</g>')
            continue

        body_parts.append(
            f'<g opacity="0" transform="translate(0, {SLIDE_DISTANCE})">'
            f'<animate attributeName="opacity" values="0;1" dur="{FADE_DURATION}s" begin="{delay:.2f}s" fill="freeze" />'
            f'<animateTransform attributeName="transform" type="translate" values="0,{SLIDE_DISTANCE};0,0" dur="{FADE_DURATION}s" begin="{delay:.2f}s" fill="freeze" />'
            f'{label_text}{value_text}'
            f'</g>'
        )

    # Footer accent line.
    body_parts.append(
        '<rect x="32" y="388" width="696" height="1" fill="#30363d" />'
    )
    body_parts.append(
        '<text x="44" y="418" fill="#56d364" font-family="Consolas, monospace" font-size="15">status: online • animated profile card</text>'
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Profile information card">
  <rect width="100%" height="100%" fill="#0d1117" />
  <g>
    {''.join(body_parts)}
  </g>
</svg>'''
    return svg


def main() -> None:
    """Write the generated SVG to the repository root."""
    OUTPUT_SVG.write_text(build_svg(), encoding="utf-8")
    print(f"Wrote {OUTPUT_SVG}")


if __name__ == "__main__":
    main()
