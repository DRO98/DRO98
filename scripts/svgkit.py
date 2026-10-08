"""Shared toolkit for the profile SVGs: palette, embedded fonts, text measuring.

Every SVG ships its own subset of Space Grotesk / JetBrains Mono as a base64
WOFF2, so the typography renders identically on any machine (images on GitHub
cannot load external fonts).
"""
from __future__ import annotations

import base64
import html
import io
import json
import re
from functools import lru_cache
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = Path(__file__).resolve().parent / "fonts"
ASSETS = ROOT / "assets"

# ── palette ────────────────────────────────────────────────────────────────
BG0 = "#07080f"
BG1 = "#0c0f1d"
PANEL = "#0f1324"
STROKE = "#1d2340"
TEXT = "#eef0fb"
MUTED = "#9aa2c7"
DIM = "#5d6590"
CYAN = "#22d3ee"
VIOLET = "#a78bfa"
PURPLE = "#7c3aed"
PINK = "#f472b6"
GREEN = "#34d399"
AMBER = "#fbbf24"

# font key -> (file, css family, css weight)
FONT_FILES = {
    "sg400": ("SpaceGrotesk-400.ttf", "SG", 400),
    "sg500": ("SpaceGrotesk-500.ttf", "SG", 500),
    "sg700": ("SpaceGrotesk-700.ttf", "SG", 700),
    "jb400": ("JetBrainsMono-400.ttf", "JB", 400),
    "jb700": ("JetBrainsMono-700.ttf", "JB", 700),
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


@lru_cache(maxsize=None)
def _font(key: str) -> TTFont:
    return TTFont(FONTS / FONT_FILES[key][0])


def measure(text: str, key: str, size: float) -> float:
    """Advance width of `text` in px for font `key` at `size`."""
    f = _font(key)
    cmap = f.getBestCmap()
    hmtx = f["hmtx"]
    upm = f["head"].unitsPerEm
    total = 0
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            raise ValueError(f"glyph {ch!r} missing in {key}")
        total += hmtx[g][0]
    return total * size / upm


def wrap(text: str, key: str, size: float, max_w: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if measure(trial, key, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _woff2_subset(key: str, chars: str) -> str:
    f = TTFont(FONTS / FONT_FILES[key][0])
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt"]
    opts.name_IDs = []
    opts.notdef_outline = True
    opts.hinting = False
    opts.desubroutinize = True
    sub = subset.Subsetter(opts)
    sub.populate(text=chars + " ")
    sub.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def _visible_text(markup: str) -> str:
    texts = re.findall(r"<text[^>]*>(.*?)</text>", markup, flags=re.S)
    raw = "".join(re.sub(r"<[^>]+>", "", t) for t in texts)
    return html.unescape(raw)


def font_css(markup: str, keys: list[str]) -> str:
    chars = "".join(sorted(set(_visible_text(markup)))) or "a"
    rules = []
    for k in keys:
        _, fam, w = FONT_FILES[k]
        rules.append(
            f"@font-face{{font-family:'{fam}';font-weight:{w};"
            f"src:url(data:font/woff2;base64,{_woff2_subset(k, chars)}) format('woff2');}}"
        )
    return "".join(rules)


BASE_CSS = f"""
.sg{{font-family:'SG',ui-sans-serif,system-ui,'Segoe UI',sans-serif}}
.jb{{font-family:'JB',ui-monospace,SFMono-Regular,Consolas,monospace}}
.w4{{font-weight:400}}.w5{{font-weight:500}}.w7{{font-weight:700}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
"""


def document(body: str, w: int, h: int, fonts: list[str], css: str = "",
             title: str = "", defs: str = "") -> str:
    style = font_css(body, fonts) + BASE_CSS + css
    style = re.sub(r"\s*\n\s*", "", style)
    t = f"<title>{esc(title)}</title>" if title else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" fill="none" role="img">{t}'
        f"<style>{style}</style><defs>{defs}</defs>{body}</svg>\n"
    )


def save(name: str, svg: str) -> None:
    path = ASSETS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    print(f"  {name:<34} {len(svg.encode()) / 1024:6.1f} KB")


@lru_cache(maxsize=None)
def icons() -> dict:
    return json.loads((Path(__file__).parent / "icons.json").read_text(encoding="utf-8"))


def icon_color(slug: str) -> str:
    """Brand colour, lifted to something readable on a near-black background."""
    hx = icons()[slug]["hex"]
    r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#e6e8f5" if lum < 0.22 else f"#{hx}"


def icon(slug: str, x: float, y: float, size: float, color: str | None = None) -> str:
    """simple-icons glyph (24×24 grid) placed at x,y with the given size."""
    d = icons()[slug]["d"]
    s = size / 24
    return (f'<path transform="translate({x:.1f} {y:.1f}) scale({s:.4f})" '
            f'd="{d}" fill="{color or icon_color(slug)}"/>')
