"""Live GitHub telemetry card -> assets/stats.svg

    GITHUB_TOKEN=... python scripts/build_stats.py [login]

Runs daily in .github/workflows/profile.yml. Only public data is used unless a
token with wider scope is provided through the STATS_TOKEN secret.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request

from svgkit import (AMBER, BG1, CYAN, DIM, GREEN, MUTED, PANEL, PINK, STROKE,
                    TEXT, VIOLET, document, esc, measure, save)

LOGIN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_REPOSITORY_OWNER", "DRO98")
SKIP_LANGS = {"Jupyter Notebook", "TeX", "Dockerfile", "Shell", "PowerShell", "CQL", "Makefile", "Batchfile"}

QUERY = """
query($login: String!) {
  user(login: $login) {
    pullRequests { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions weeks { contributionDays { contributionCount } } }
    }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
      nodes { stargazerCount languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
        edges { size node { name color } } } }
    }
  }
}"""


def token() -> str:
    for var in ("STATS_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def fetch() -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token()}", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(payload["errors"])
    return payload["data"]["user"]


# ── drawing ────────────────────────────────────────────────────────────────

DIGIT_FS = 54
LH = 64


def odometer(x: float, baseline: float, value: int, delay: float, uid: str, css: list[str]) -> str:
    text = f"{value:,}"
    col_w = max(measure(d, "sg700", DIGIT_FS) for d in "0123456789")
    out = []
    cx = x
    for k, ch in enumerate(text):
        if not ch.isdigit():
            out.append(f'<text x="{cx:.1f}" y="{baseline}" class="sg w7" font-size="{DIGIT_FS}" fill="{TEXT}">{ch}</text>')
            cx += measure(ch, "sg700", DIGIT_FS)
            continue
        d = int(ch)
        cid = f"{uid}{k}"
        strip = "".join(
            f'<text x="{cx + col_w / 2:.1f}" y="{baseline + i * LH}" text-anchor="middle" class="sg w7" '
            f'font-size="{DIGIT_FS}" fill="{TEXT}">{i % 10}</text>' for i in range(20))
        out.append(f'<clipPath id="k{cid}"><rect x="{cx - 2:.1f}" y="{baseline - DIGIT_FS + 4}" width="{col_w + 4:.1f}" '
                   f'height="{LH}"/></clipPath><g clip-path="url(#k{cid})"><g class="r{cid}">{strip}</g></g>')
        dist = (10 + d) * LH
        css.append(f".r{cid}{{animation:r{cid} {2.0 + k * .18:.2f}s cubic-bezier(.12,.8,.22,1) {delay:.2f}s both}}"
                   f"@keyframes r{cid}{{from{{transform:translateY(0)}}to{{transform:translateY(-{dist}px)}}}}")
        cx += col_w
    return "".join(out)


def build(u: dict) -> str:
    W, H = 1200, 452
    cc = u["contributionsCollection"]
    weeks = cc["contributionCalendar"]["weeks"]
    weekly = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks][-26:]
    repos = u["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in repos)
    kpis = [
        ("CONTRIBUTIONS", cc["contributionCalendar"]["totalContributions"], "last 12 months", CYAN),
        ("COMMITS", cc["totalCommitContributions"], "last 12 months", VIOLET),
        ("PULL REQUESTS", u["pullRequests"]["totalCount"], "all time", PINK),
        ("PUBLIC REPOS", u["repositories"]["totalCount"], f"{stars} star{'s' if stars != 1 else ''} earned", GREEN),
    ]
    langs: dict[str, list] = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            if name in SKIP_LANGS:
                continue
            langs.setdefault(name, [0, e["node"]["color"] or "#888888"])[0] += e["size"]
    ranked = sorted(langs.items(), key=lambda kv: -kv[1][0])
    total = sum(v[0] for _, v in ranked) or 1
    top = ranked[:6]
    other = total - sum(v[0] for _, v in top)
    if other > 0:
        top.append(("Other", [other, "#4b5277"]))

    css: list[str] = []
    parts = [f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="{BG1}"/>']

    # KPI tiles
    pad, gap = 24, 14
    tw = (W - 2 * pad - 3 * gap) / 4
    for i, (label, value, sub, col) in enumerate(kpis):
        x = pad + i * (tw + gap)
        parts.append(
            f'<rect x="{x:.1f}" y="{pad}" width="{tw:.1f}" height="150" rx="18" fill="{PANEL}" stroke="{STROKE}"/>'
            f'<rect x="{x:.1f}" y="{pad}" width="{tw:.1f}" height="150" rx="18" fill="url(#t{i})"/>'
            f'<circle cx="{x + 26:.1f}" cy="{pad + 30}" r="4" fill="{col}"/>'
            f'<text x="{x + 38:.1f}" y="{pad + 35}" class="jb w7" font-size="12.5" letter-spacing="1.6" fill="{MUTED}">{label}</text>'
            f'{odometer(x + 22, pad + 104, value, .2 + i * .15, f"n{i}", css)}'
            f'<text x="{x + 24:.1f}" y="{pad + 133}" class="jb w4" font-size="13" fill="{DIM}">{esc(sub)}</text>')

    # contributions chart
    cy0 = pad + 150 + gap
    ch_h = H - cy0 - pad
    cw_ = 650
    parts.append(f'<rect x="{pad}" y="{cy0}" width="{cw_}" height="{ch_h}" rx="18" fill="{PANEL}" stroke="{STROKE}"/>'
                 f'<text x="{pad + 24}" y="{cy0 + 34}" class="jb w7" font-size="12.5" letter-spacing="1.6" fill="{MUTED}">'
                 f'WEEKLY CONTRIBUTIONS · LAST 26 WEEKS</text>')
    gx0, gx1 = pad + 24, pad + cw_ - 24
    gy0, gy1 = cy0 + 60, cy0 + ch_h - 26
    peak = max(weekly) or 1
    scale = lambda v: (v / peak) ** 0.5  # sqrt keeps quiet weeks visible next to a spike
    for g in range(4):
        y = gy0 + g * (gy1 - gy0) / 3
        parts.append(f'<path d="M{gx0} {y:.1f}H{gx1}" stroke="#fff" stroke-opacity=".05" stroke-dasharray="3 5"/>')
    n = len(weekly)
    pts = [(gx0 + k * (gx1 - gx0) / (n - 1), gy1 - scale(v) * (gy1 - gy0)) for k, v in enumerate(weekly)]
    # smooth with Catmull-Rom → cubic bezier
    sm = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for k in range(n - 1):
        p0, p1, p2, p3 = pts[max(k - 1, 0)], pts[k], pts[k + 1], pts[min(k + 2, n - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, min(gy1, p1[1] + (p2[1] - p0[1]) / 6))
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, min(gy1, p2[1] - (p3[1] - p1[1]) / 6))
        sm += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    area = sm + f" L{gx1} {gy1} L{gx0} {gy1} Z"
    pk = max(range(n), key=lambda k: weekly[k])
    px, py = pts[pk]
    parts.append(f'<path class="area" d="{area}" fill="url(#ar)"/>'
                 f'<path class="line" d="{sm}" pathLength="1" stroke="url(#ln)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<g class="peak"><circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{PINK}"/>'
                 f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="none" stroke="{PINK}" stroke-width="1.5">'
                 f'<animate attributeName="r" values="5;16" dur="2s" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values=".8;0" dur="2s" repeatCount="indefinite"/></circle>'
                 f'<text x="{min(px, gx1 - 60):.1f}" y="{max(py - 14, gy0 - 8):.1f}" text-anchor="middle" class="jb w7" font-size="13" fill="{PINK}">'
                 f'peak {weekly[pk]}</text></g>')

    # languages
    lx = pad + cw_ + gap
    lw = W - pad - lx
    parts.append(f'<rect x="{lx}" y="{cy0}" width="{lw}" height="{ch_h}" rx="18" fill="{PANEL}" stroke="{STROKE}"/>'
                 f'<text x="{lx + 24}" y="{cy0 + 34}" class="jb w7" font-size="12.5" letter-spacing="1.6" fill="{MUTED}">'
                 f'LANGUAGES · PUBLIC CODE</text>')
    bx, bw, by = lx + 24, lw - 48, cy0 + 56
    segs, x = [], bx
    for name, (size, color) in top:
        w = bw * size / total
        segs.append(f'<rect x="{x:.1f}" y="{by}" width="{max(w - 3, 1):.1f}" height="14" rx="4" fill="{color}"/>')
        x += w
    parts.append(f'<clipPath id="bar"><rect x="{bx}" y="{by}" width="0" height="14" rx="7">'
                 f'<animate attributeName="width" to="{bw}" begin=".5s" dur="1.6s" fill="freeze" calcMode="spline" '
                 f'keySplines=".2 .8 .2 1" keyTimes="0;1"/></rect></clipPath>'
                 f'<rect x="{bx}" y="{by}" width="{bw}" height="14" rx="7" fill="#fff" fill-opacity=".05"/>'
                 f'<g clip-path="url(#bar)">{"".join(segs)}</g>')
    col_w = bw / 2
    for k, (name, (size, color)) in enumerate(top):
        cx = bx + (k % 2) * col_w
        cy = by + 52 + (k // 2) * 34
        pct = f"{100 * size / total:.1f}%"
        parts.append(f'<g class="lg" style="animation-delay:{.9 + k * .08:.2f}s">'
                     f'<circle cx="{cx + 6:.1f}" cy="{cy - 5}" r="6" fill="{color}"/>'
                     f'<text x="{cx + 20:.1f}" y="{cy}" class="sg w5" font-size="17" fill="{TEXT}">{esc(name)}</text>'
                     f'<text x="{cx + col_w - 16:.1f}" y="{cy}" text-anchor="end" class="jb w4" font-size="14" fill="{MUTED}">{pct}</text></g>')

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts.append(f'<text x="{W - pad - 24}" y="{cy0 + ch_h - 22}" text-anchor="end" class="jb w4" font-size="12" fill="{DIM}">'
                 f'synced {stamp}</text>')

    defs = [f'<linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".35"/>'
            f'<stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>',
            f'<linearGradient id="ln" x1="{gx0}" y1="0" x2="{gx1}" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{CYAN}"/>'
            f'<stop offset=".6" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>']
    for i, (*_, col) in enumerate(kpis):
        defs.append(f'<linearGradient id="t{i}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{col}" stop-opacity=".1"/>'
                    f'<stop offset=".6" stop-color="{col}" stop-opacity="0"/></linearGradient>')
    css.append(".line{stroke-dasharray:1;stroke-dashoffset:1;animation:dr 2.4s cubic-bezier(.4,0,.2,1) .4s forwards}"
               "@keyframes dr{to{stroke-dashoffset:0}}"
               ".area{opacity:0;animation:fi 1.2s ease 1.6s forwards}.peak{opacity:0;animation:fi .6s ease 2.6s forwards}"
               ".lg{opacity:0;animation:fi .6s ease forwards}@keyframes fi{to{opacity:1}}")
    return document("".join(parts), W, H, ["sg500", "sg700", "jb400", "jb700"], "".join(css),
                    f"GitHub telemetry for {LOGIN}", "".join(defs))


if __name__ == "__main__":
    data = fetch()
    save("stats.svg", build(data))
