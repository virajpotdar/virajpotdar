#!/usr/bin/env python3
"""Generate an animated monochrome ASCII portrait SVG from an image."""
from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
INPUT_IMAGE = ROOT / "source-prepped.png"
OUTPUT_SVG = ROOT / "avi-ascii.svg"

RAMP = " .'`:-=+*cs#%@"
WIDTH_CHARS = 100
HEIGHT_CHARS = 53
FONT_SIZE = 10
CHAR_SPACING = 7.2
LINE_HEIGHT = 12
CURSOR_WIDTH = 6
CURSOR_HEIGHT = 12


def load_image(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"Input image not found: {path}")
    with Image.open(path) as img:
        return img.convert("L")


def resize_for_canvas(img: Image.Image, width_chars: int, height_chars: int) -> Image.Image:
    target_width = width_chars
    target_height = height_chars
    img_width, img_height = img.size
    aspect = img_width / img_height
    if img_width / target_width > img_height / target_height:
        new_width = target_width
        new_height = max(1, int(target_width / aspect))
    else:
        new_height = target_height
        new_width = max(1, int(target_height * aspect))
    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def create_ascii_rows(img: Image.Image, width_chars: int, height_chars: int) -> list[str]:
    resized = resize_for_canvas(img, width_chars, height_chars)
    width, height = resized.size
    rows: list[str] = []
    for y in range(height):
        chars = []
        for x in range(width):
            pixel = resized.getpixel((x, y))
            if pixel < 32:
                chars.append("#")
            elif pixel < 96:
                chars.append("@")
            else:
                idx = int(pixel / 255 * (len(RAMP) - 1))
                chars.append(RAMP[idx])
        rows.append("".join(chars))
    return rows


def build_svg(rows: list[str]) -> str:
    width = WIDTH_CHARS * CHAR_SPACING + 12
    height = len(rows) * LINE_HEIGHT + 16
    view_box = f"0 0 {width:.2f} {height:.2f}"

    body_parts = []
    line_y = 8
    for row_index, row in enumerate(rows):
        chars = list(row)
        x_pos = 8
        for char_index, ch in enumerate(chars):
            if ch == " ":
                x_pos += CHAR_SPACING
                continue
            body_parts.append(
                f'<text x="{x_pos:.2f}" y="{line_y:.2f}" fill="#f5f5f5" font-family="Courier New, Consolas, monospace" font-size="{FONT_SIZE}" dominant-baseline="hanging">{escape(ch)}</text>'
            )
            x_pos += CHAR_SPACING
        line_y += LINE_HEIGHT

    cursor_x = 8 + len(rows[0]) * CHAR_SPACING if rows else 8
    cursor_y = 8
    cursor = (
        f'<rect x="{cursor_x:.2f}" y="{cursor_y:.2f}" width="{CURSOR_WIDTH}" height="{CURSOR_HEIGHT}" fill="#f5f5f5">'
        '<animate attributeName="opacity" values="1;1;0" dur="0.8s" repeatCount="1" />'
        '</rect>'
    )

    reveal_parts = []
    for row_index, row in enumerate(rows):
        text_x = 8
        for char_index, ch in enumerate(list(row)):
            if ch == " ":
                text_x += CHAR_SPACING
                continue
            reveal_parts.append(
                f'<g opacity="0">'
                f'<animate attributeName="opacity" values="0;1" begin="{(row_index * 0.04 + char_index * 0.005):.3f}s" dur="0.06s" fill="freeze"/>'
                f'<text x="{text_x:.2f}" y="{8 + row_index * LINE_HEIGHT:.2f}" fill="#f5f5f5" font-family="Courier New, Consolas, monospace" font-size="{FONT_SIZE}" dominant-baseline="hanging">{escape(ch)}</text>'
                f'</g>'
            )
            text_x += CHAR_SPACING

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="auto" viewBox="{view_box}" role="img" aria-label="ASCII portrait animation">
  <rect width="100%" height="100%" fill="#0b0f14" />
  <g font-family="Courier New, Consolas, monospace" font-size="{FONT_SIZE}" fill="#f5f5f5">
    {''.join(reveal_parts)}
  </g>
  <g>
    {cursor}
  </g>
</svg>'''
    return svg


def main() -> None:
    if not INPUT_IMAGE.exists():
        print(f"Input image not found: {INPUT_IMAGE}")
        print("Creating a simple placeholder SVG instead.")
        placeholder = '''<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="auto" viewBox="0 0 700 700" role="img" aria-label="Placeholder ASCII portrait">
  <rect width="100%" height="100%" fill="#0b0f14" />
  <text x="20" y="40" fill="#f5f5f5" font-family="Courier New, Consolas, monospace" font-size="24">ASCII portrait placeholder</text>
</svg>'''
        OUTPUT_SVG.write_text(placeholder, encoding="utf-8")
        return

    img = load_image(INPUT_IMAGE)
    rows = create_ascii_rows(img, WIDTH_CHARS, HEIGHT_CHARS)
    svg = build_svg(rows)
    OUTPUT_SVG.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUTPUT_SVG}")


if __name__ == "__main__":
    main()
