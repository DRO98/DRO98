"""Generates every static SVG used by the profile README.

    python scripts/build_assets.py

Stats are live and come from scripts/build_stats.py (run daily by a workflow).
"""
from __future__ import annotations

import math
import random

from svgkit import (AMBER, BG0, BG1, CYAN, DIM, GREEN, MUTED, PANEL, PINK,
                    PURPLE, STROKE, TEXT, VIOLET, document, esc, icon,
                    icon_color, measure, save, wrap)

# ── helpers ────────────────────────────────────────────────────────────────


def typing_anim(n_chars: int, cw: float, begin: float, T: float | None = None,
                 cps: float = 18, hold: float = 0.0, delete_cps: float = 45,
                 attr: str = "width") -> str:
    """Discrete SMIL animation that reveals `n_chars` monospace chars one by one.

    With T=None it plays once and freezes. With T it loops every T seconds:
    type, hold, delete, stay hidden until the cycle ends.
    """
    pts: list[tuple[float, float]] = [(0.0, 0.0)]
    t = begin
    for k in range(n_chars + 1):
        pts.append((t, k * cw))
        t += 1 / cps
    if T is not None:
        t += hold
        for k in range(n_chars, -1, -1):
            pts.append((t, k * cw))
            t += 1 / delete_cps
        assert t < T, (t, T)
    total = T if T is not None else t
    keys, vals = [], []
    for tt, v in pts:
        kt = round(tt / total, 5)
        if keys and kt <= keys[-1]:
            keys[-1], vals[-1] = kt, v
            continue
        keys.append(kt)
        vals.append(v)
    if T is None:
        keys[-1] = 1.0
        return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{total:.3f}s" '
                f'fill="freeze" keyTimes="{";".join(map(str, keys))}" '
                f'values="{";".join(f"{v:.1f}" for v in vals)}"/>')
    return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{T}s" '
            f'repeatCount="indefinite" keyTimes="{";".join(map(str, keys))}" '
            f'values="{";".join(f"{v:.1f}" for v in vals)}"/>')


def spaced_width(text: str, key: str, size: float, ls: float) -> float:
    return measure(text, key, size) + ls * len(text)


LIGHT = {TEXT: "#1f2328", MUTED: "#59636e", DIM: "#8c959f"}


def save_themed(name: str, svg: str) -> None:
    """Saves a dark version and a `-light` twin for elements without their own background."""
    save(name, svg)
    for dark, light in LIGHT.items():
        svg = svg.replace(f'"{dark}"', f'"{light}"')
    save(name.replace(".svg", "-light.svg"), svg)


ROTATE_BORDER = ('<animateTransform attributeName="gradientTransform" type="rotate" '
                 'from="0 .5 .5" to="360 .5 .5" dur="{dur}s" repeatCount="indefinite"/>')


# ── 1. hero header ─────────────────────────────────────────────────────────

ROLES = [
    "Data Systems Engineer @ UPM",
    "Founder & dev of Sportimizer ERP",
    "2x hackathon winner: BeTech, IndesIA",
    "Building auditable AI systems",
    "Turning data into decisions",
]


def header() -> None:
    W, H = 1200, 470
    rnd = random.Random(98)

    # data-graph constellation on the right
    nodes = []
    while len(nodes) < 22:
        p = (rnd.uniform(760, 1150), rnd.uniform(60, 410))
        if all(math.dist(p, q) > 58 for q in nodes):
            nodes.append(p)
    edges = set()
    for i, p in enumerate(nodes):
        near = sorted(range(len(nodes)), key=lambda j: math.dist(p, nodes[j]))[1:3]
        for j in near:
            edges.add(tuple(sorted((i, j))))
    adj = {i: [] for i in range(len(nodes))}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)

    graph = []
    for a, b in sorted(edges):
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        graph.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'stroke="url(#edge)" stroke-width="1.1"/>')
    hubs = {0, 5, 11, 17}
    for i, (x, y) in enumerate(nodes):
        r = 4.6 if i in hubs else rnd.uniform(1.8, 3.2)
        col = [CYAN, VIOLET, PINK][i % 3]
        delay = rnd.uniform(0, 4)
        graph.append(f'<circle class="pulse" style="animation-delay:{delay:.2f}s" cx="{x:.1f}" '
                     f'cy="{y:.1f}" r="{r:.1f}" fill="{col}"/>')
        if i in hubs:
            graph.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="none" stroke="{col}" stroke-width="1.5">'
                f'<animate attributeName="r" values="5;26" dur="3s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values=".8;0" dur="3s" begin="{delay:.2f}s" repeatCount="indefinite"/>'
                f'</circle>')
    # packets travelling along random walks through the graph
    for k in range(7):
        cur = rnd.randrange(len(nodes))
        walk = [cur]
        for _ in range(5):
            nxt = [n for n in adj[cur] if n not in walk] or adj[cur]
            cur = rnd.choice(nxt)
            walk.append(cur)
        d = "M" + " L".join(f"{nodes[n][0]:.1f} {nodes[n][1]:.1f}" for n in walk)
        col = [CYAN, PINK, VIOLET, GREEN][k % 4]
        dur = rnd.uniform(4.5, 7.5)
        graph.append(
            f'<circle r="3.2" fill="{col}" filter="url(#glow)">'
            f'<animateMotion dur="{dur:.2f}s" begin="{k * 0.7:.1f}s" repeatCount="indefinite" path="{d}"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.9;1" dur="{dur:.2f}s" '
            f'begin="{k * 0.7:.1f}s" repeatCount="indefinite"/></circle>')

    # location pill
    pill_txt = "MADRID, ES  ·  DATA SYSTEMS ENG. @ UPM"
    pw = spaced_width(pill_txt, "jb400", 14, 1.6) + 56
    pill = (f'<g class="rise" style="animation-delay:.1s">'
            f'<rect x="68" y="62" width="{pw:.1f}" height="36" rx="18" fill="#ffffff" fill-opacity=".04" stroke="{STROKE}"/>'
            f'<circle cx="90" cy="80" r="4.5" fill="{GREEN}"/>'
            f'<circle cx="90" cy="80" r="4.5" fill="none" stroke="{GREEN}" stroke-width="1.5">'
            f'<animate attributeName="r" values="4.5;12" dur="2s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values=".9;0" dur="2s" repeatCount="indefinite"/></circle>'
            f'<text x="106" y="85" class="jb w4" font-size="14" letter-spacing="1.6" fill="{MUTED}">{esc(pill_txt)}</text></g>')

    name = (f'<g class="rise" style="animation-delay:.25s">'
            f'<text x="62" y="210" class="sg w7" font-size="96" letter-spacing="-2.5" fill="{TEXT}">Alejandro</text></g>'
            f'<g class="rise" style="animation-delay:.4s">'
            f'<text x="62" y="304" class="sg w7" font-size="96" letter-spacing="-2.5" fill="url(#nameGrad)">'
            f'Cuevas Cid<tspan fill="{CYAN}">.</tspan></text></g>')

    # cycling typewriter roles
    fs, cw = 25, 0.6 * 25
    prompt = "~ $ "
    x0 = 68 + measure(prompt, "jb700", fs)
    slot = 4.2
    T = slot * len(ROLES)
    typer = [f'<text x="68" y="368" class="jb w7" font-size="{fs}" fill="{GREEN}">{esc(prompt)}</text>']
    for i, role in enumerate(ROLES):
        n = len(role)
        t0 = i * slot
        hold = slot - n / 18 - (n + 1) / 45 - 0.25
        typer.append(
            f'<clipPath id="tc{i}"><rect x="{x0:.1f}" y="335" width="0" height="46">'
            f'{typing_anim(n, cw, t0, T, hold=hold)}</rect></clipPath>'
            f'<text clip-path="url(#tc{i})" x="{x0:.1f}" y="368" class="jb w4" font-size="{fs}" '
            f'fill="{TEXT}">{esc(role)}</text>')
        vis_keys = sorted({0.0, round(t0 / T, 5), round((t0 + slot) / T, 5)})
        vis_vals = {0.0: "0"}
        vis_vals[round(t0 / T, 5)] = "1"
        vis_vals[round((t0 + slot) / T, 5)] = "0"
        if (t0 + slot) / T >= 1:
            vis_keys = [k for k in vis_keys if k < 1]
        vals = ";".join(vis_vals[k] for k in vis_keys)
        typer.append(
            f'<g opacity="0"><animate attributeName="opacity" calcMode="discrete" dur="{T}s" '
            f'repeatCount="indefinite" keyTimes="{";".join(map(str, vis_keys))}" values="{vals}"/>'
            f'<rect class="blink" x="{x0 + 2:.1f}" y="347" width="{cw * 0.62:.1f}" height="27" rx="2" fill="{CYAN}">'
            f'{typing_anim(n, cw, t0, T, hold=hold, attr="x").replace("values=", "additive=\"sum\" values=")}'
            f'</rect></g>')

    meta = ["data engineering", "applied AI", "founder @ sportimizer", "5x first prize"]
    mx = 68
    meta_svg = [f'<g class="rise" style="animation-delay:.7s">']
    meta_svg.append(f'<rect x="{mx}" y="414" width="34" height="2" rx="1" fill="url(#nameGrad)"/>')
    mx += 48
    for i, m in enumerate(meta):
        meta_svg.append(f'<text x="{mx:.1f}" y="421" class="jb w4" font-size="15" fill="{MUTED}">{esc(m)}</text>')
        mx += measure(m, "jb400", 15)
        if i < len(meta) - 1:
            meta_svg.append(f'<circle cx="{mx + 14:.1f}" cy="416" r="2.5" fill="{[CYAN, VIOLET, PINK][i]}"/>')
            mx += 28
    meta_svg.append("</g>")

    defs = f"""
<clipPath id="frame"><rect width="{W}" height="{H}" rx="28"/></clipPath>
<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="70"/></filter>
<filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="3" result="b"/>
<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="nameGrad" x1="60" y1="0" x2="640" y2="0" gradientUnits="userSpaceOnUse" spreadMethod="reflect">
<stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/>
<animateTransform attributeName="gradientTransform" type="translate" values="0 0;580 0;0 0" dur="9s" repeatCount="indefinite"/>
</linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity=".35"/>
<stop offset="1" stop-color="{VIOLET}" stop-opacity=".18"/></linearGradient>
<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.1" fill="#ffffff" fill-opacity=".07"/></pattern>
<radialGradient id="fade" cx=".72" cy=".45" r=".7"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
<mask id="dotmask"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/>
<stop offset=".5" stop-color="{CYAN}" stop-opacity=".07"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>
<linearGradient id="rim" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity=".55"/>
<stop offset=".35" stop-color="{STROKE}"/><stop offset=".7" stop-color="{STROKE}"/><stop offset="1" stop-color="{PINK}" stop-opacity=".55"/>
{ROTATE_BORDER.format(dur=14)}</linearGradient>
"""
    css = """
.b1{animation:d1 17s ease-in-out infinite alternate}
.b2{animation:d2 21s ease-in-out infinite alternate}
.b3{animation:d3 19s ease-in-out infinite alternate}
@keyframes d1{to{transform:translate(260px,90px)}}
@keyframes d2{to{transform:translate(-300px,-60px)}}
@keyframes d3{to{transform:translate(-180px,110px)}}
.pulse{animation:pl 4s ease-in-out infinite}
@keyframes pl{0%,100%{opacity:.45}50%{opacity:1}}
.scan{animation:sc 7s linear infinite}
@keyframes sc{from{transform:translateY(-140px)}to{transform:translateY(480px)}}
.rise{animation:rs 1.1s cubic-bezier(.2,.8,.2,1) both}
@keyframes rs{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:none}}
.blink{animation:bk 1s steps(1) infinite}
@keyframes bk{50%{opacity:0}}
"""
    body = f"""
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="{BG0}"/>
<g filter="url(#blur)" opacity=".55">
<circle class="b1" cx="180" cy="80" r="200" fill="{PURPLE}"/>
<circle class="b2" cx="980" cy="380" r="220" fill="{CYAN}" fill-opacity=".75"/>
<circle class="b3" cx="760" cy="40" r="170" fill="{PINK}" fill-opacity=".6"/>
</g>
<rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#dotmask)"/>
<rect class="scan" y="0" width="{W}" height="140" fill="url(#scan)"/>
<g>{"".join(graph)}</g>
{pill}{name}{"".join(typer)}{"".join(meta_svg)}
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="27.5" stroke="url(#rim)" stroke-width="1.5"/>
"""
    save("header.svg", document(body, W, H, ["sg700", "jb400", "jb700"], css,
                                "Alejandro Cuevas Cid — Data Systems Engineer", defs))


# ── 2. section titles ──────────────────────────────────────────────────────

SECTIONS = [
    ("01", "About me", "whoami"),
    ("02", "Featured work", "selected projects"),
    ("03", "Data engineering lab", "stream → process → orchestrate → observe"),
    ("04", "Tech stack", "tools I ship with"),
    ("05", "Recognition", "2020 → 2026"),
    ("06", "Live telemetry", "auto-updated daily"),
]


def section_titles() -> None:
    W, H = 1200, 84
    for num, title, caption in SECTIONS:
        x = 4
        parts = [f'<text x="{x}" y="56" class="jb w7" font-size="20" fill="url(#g)">{num}</text>']
        x += measure(num, "jb700", 20) + 14
        parts.append(f'<text x="{x:.1f}" y="56" class="jb w4" font-size="20" fill="{DIM}">/</text>')
        x += measure("/", "jb400", 20) + 14
        parts.append(f'<text x="{x:.1f}" y="58" class="sg w7" font-size="38" letter-spacing="-.8" fill="{TEXT}">{esc(title)}</text>')
        x += measure(title, "sg700", 38) - 0.8 * len(title) + 26
        cap_w = measure(caption, "jb400", 15)
        line_end = W - cap_w - 26
        length = line_end - x
        parts.append(
            f'<path d="M{x:.1f} 46 H{line_end:.1f}" stroke="url(#g)" stroke-width="2" stroke-linecap="round" '
            f'stroke-dasharray="{length:.1f}" stroke-dashoffset="{length:.1f}">'
            f'<animate attributeName="stroke-dashoffset" to="0" dur="1.6s" begin=".2s" fill="freeze" '
            f'calcMode="spline" keySplines=".2 .8 .2 1" keyTimes="0;1"/></path>'
            f'<circle r="3.5" fill="{CYAN}" filter="url(#glow)" opacity="0">'
            f'<animate attributeName="opacity" to="1" begin="1.8s" dur=".1s" fill="freeze"/>'
            f'<animateMotion path="M{x:.1f} 46 H{line_end:.1f}" dur="4.5s" begin="1.8s" repeatCount="indefinite"/></circle>'
            f'<text x="{W - 4}" y="51" text-anchor="end" class="jb w4" font-size="15" fill="{MUTED}">{esc(caption)}</text>')
        defs = (f'<linearGradient id="g" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse">'
                f'<stop offset="0" stop-color="{CYAN}"/><stop offset=".55" stop-color="{VIOLET}"/>'
                f'<stop offset="1" stop-color="{PINK}" stop-opacity=".25"/></linearGradient>'
                f'<filter id="glow" x="-300%" y="-300%" width="700%" height="700%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
                f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
        slug = title.lower().replace(" ", "-")
        save_themed(f"sections/{num}-{slug}.svg",
             document("".join(parts), W, H, ["sg700", "jb400", "jb700"], "", f"{num} {title}", defs))


# ── 3. contact buttons ─────────────────────────────────────────────────────

LINKEDIN = ('<rect x="{x}" y="{y}" width="30" height="30" rx="7" fill="#0A66C2"/>'
            '<text x="{tx}" y="{ty}" text-anchor="middle" class="sg w7" font-size="19" fill="#fff">in</text>')
MAIL = ('<g stroke="{c}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">'
        '<rect x="{x}" y="{y1}" width="30" height="22" rx="4"/><path d="M{x} {y2} l15 10 l15 -10"/></g>')
GLOBE = ('<g stroke="{c}" stroke-width="2.2"><circle cx="{cx}" cy="{cy}" r="14"/>'
         '<ellipse cx="{cx}" cy="{cy}" rx="6.5" ry="14"/><path d="M{l} {cy} h28 M{l2} {t} h22 M{l2} {b} h22"/></g>')


def buttons() -> None:
    W, H = 300, 72
    specs = [
        ("linkedin", "LinkedIn", "#0A66C2"),
        ("portfolio", "Portfolio", CYAN),
        ("email", "Email me", PINK),
    ]
    for slug, label, col in specs:
        ix, iy = 26, 21
        if slug == "linkedin":
            glyph = LINKEDIN.format(x=ix, y=iy, tx=ix + 15, ty=iy + 22)
        elif slug == "email":
            glyph = MAIL.format(c=col, x=ix, y1=iy + 4, y2=iy + 7)
        else:
            cx, cy = ix + 15, iy + 15
            glyph = GLOBE.format(c=col, cx=cx, cy=cy, l=cx - 14, l2=cx - 11,
                                 t=cy - 7, b=cy + 7)
        tw = measure(label, "sg500", 24)
        arrow_x = 74 + tw + 14
        body = f"""
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="{PANEL}"/>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="url(#tint)"/>
<g clip-path="url(#c)"><rect class="shine" x="-120" y="-20" width="70" height="{H + 40}" fill="url(#sh)" transform="skewX(-20)"/></g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" stroke="url(#bd)" stroke-width="1.6"/>
{glyph}
<text x="74" y="44" class="sg w5" font-size="24" fill="{TEXT}">{esc(label)}</text>
<path d="M{arrow_x:.1f} 42 l9 -9 M{arrow_x + 2:.1f} 33 h7 v7" stroke="{MUTED}" stroke-width="2" stroke-linecap="round" fill="none"/>
"""
        defs = f"""
<clipPath id="c"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20"/></clipPath>
<linearGradient id="tint" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{col}" stop-opacity=".16"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient>
<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".13"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="bd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{col}"/><stop offset=".5" stop-color="{STROKE}"/><stop offset="1" stop-color="{col}" stop-opacity=".5"/>{ROTATE_BORDER.format(dur=6)}</linearGradient>
"""
        css = (".shine{animation:sh 4.5s ease-in-out infinite}"
               "@keyframes sh{0%,55%{transform:skewX(-20deg) translateX(0)}100%{transform:skewX(-20deg) translateX(560px)}}")
        save(f"buttons/{slug}.svg", document(body, W, H, ["sg500", "sg700"], css, label, defs))


# ── 4. terminal "whoami" ───────────────────────────────────────────────────

C_KEY, C_STR, C_CMT = VIOLET, AMBER, DIM
TERMINAL = [
    ("cmd", "whoami"),
    ("out", [("Alejandro Cuevas Cid", TEXT), (" — Data Systems Engineering student, 4th year", MUTED)]),
    ("out", [("ETSIT · Universidad Politécnica de Madrid", MUTED), ("  (2023 → 2027)", C_CMT)]),
    ("gap", None),
    ("cmd", "cat profile.yml"),
    ("out", [("focus:     ", C_KEY), ("[data engineering, applied AI, data platforms]", TEXT)]),
    ("out", [("building:  ", C_KEY), ("Sportimizer", GREEN), (" — the ERP for Spanish sports clubs", TEXT)]),
    ("out", [("impact:    ", C_KEY), ("-6 h/week admin work · -15-20% operational errors", TEXT)]),
    ("out", [("cloud:     ", C_KEY), ("AWS · Docker · Kubernetes", TEXT)]),
    ("out", [("speaks:    ", C_KEY), ("spanish (native) · english (C1)", TEXT)]),
    ("out", [("superpower:", C_KEY), (' "explaining trade-offs to tech & non-tech people"', C_STR)]),
    ("gap", None),
    ("cmd", "ls ./trophies"),
    ("out", [("BeTech_2025  IndesIA_2025  YouthIGF_2024  EdwingEd_2020  ", GREEN),
             ("ActuaUPM_2026/", CYAN)]),
    ("prompt", None),
]


def terminal() -> None:
    W = 1200
    fs, lh = 20, 33
    cw = 0.6 * fs
    top = 64
    rows = [r for r in TERMINAL]
    H = top + 34 + sum(lh if k != "gap" else 14 for k, _ in rows) - 4
    prompt = "➜ ~ "
    try:
        measure(prompt, "jb700", fs)
    except ValueError:
        prompt = "> ~ "
    pw = measure(prompt, "jb700", fs)
    parts = []
    y = top + 44
    t = 0.6
    x0 = 44
    for kind, content in rows:
        if kind == "gap":
            y += 14
            t += 0.15
            continue
        if kind in ("cmd", "prompt"):
            parts.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                         f'<text x="{x0}" y="{y}" class="jb w7" font-size="{fs}" fill="{GREEN}">{esc(prompt)}</text></g>')
            if kind == "prompt":
                parts.append(f'<rect class="blink" x="{x0 + pw + 2:.1f}" y="{y - 18}" width="{cw * .62:.1f}" height="23" '
                             f'rx="2" fill="{CYAN}" opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/></rect>')
                break
            n = len(content)
            cid = f"c{y}"
            parts.append(f'<clipPath id="{cid}"><rect x="{x0 + pw:.1f}" y="{y - 26}" width="0" height="36">'
                         f'{typing_anim(n, cw, t + 0.25, cps=22)}</rect></clipPath>'
                         f'<text clip-path="url(#{cid})" x="{x0 + pw:.1f}" y="{y}" class="jb w4" font-size="{fs}" '
                         f'fill="{TEXT}">{esc(content)}</text>')
            t += 0.25 + n / 22 + 0.35
        else:
            spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in content)
            total = sum(len(s) for s, _ in content)
            assert total * cw < W - 2 * x0, (total, content)
            parts.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{t:.2f}s" dur=".35s" fill="freeze"/>'
                         f'<text x="{x0}" y="{y}" class="jb w4" font-size="{fs}" xml:space="preserve">{spans}</text></g>')
            t += 0.11
        y += lh

    chrome = f"""
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="{BG1}"/>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="url(#glowbg)"/>
<path d="M1 21a20 20 0 0 1 20-20h{W - 42}a20 20 0 0 1 20 20v{top - 21}H1z" fill="#ffffff" fill-opacity=".025"/>
<path d="M1 {top}H{W - 1}" stroke="{STROKE}"/>
<circle cx="34" cy="{top / 2}" r="7" fill="#ff5f57"/><circle cx="58" cy="{top / 2}" r="7" fill="#febc2e"/><circle cx="82" cy="{top / 2}" r="7" fill="#28c840"/>
<text x="{W / 2}" y="{top / 2 + 5}" text-anchor="middle" class="jb w4" font-size="15" fill="{DIM}">alejandro@madrid — ~/profile — zsh</text>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" stroke="url(#bd)" stroke-width="1.5"/>
"""
    defs = f"""
<radialGradient id="glowbg" cx="1" cy="0" r="1"><stop offset="0" stop-color="{PURPLE}" stop-opacity=".16"/><stop offset=".6" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>
<linearGradient id="bd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".7"/><stop offset=".4" stop-color="{STROKE}"/><stop offset=".75" stop-color="{STROKE}"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".6"/>{ROTATE_BORDER.format(dur=12)}</linearGradient>
"""
    css = ".blink{animation:bk 1s steps(1) infinite}@keyframes bk{50%{fill-opacity:0}}"
    save("about.svg", document(chrome + "".join(parts), W, H, ["jb400", "jb700"], css,
                               "whoami — Alejandro Cuevas Cid", defs))


# ── 5. project cards ───────────────────────────────────────────────────────

PROJECTS = [
    dict(
        file="sportimizer", title="Sportimizer ERP", glyph="django",
        tag="FOUNDER · 2024 → NOW", tag_c=GREEN, a=GREEN, b=CYAN,
        desc="All-in-one ERP for Spanish sports clubs: players & families, coaches, physio, "
             "leagues, accounting, inventory and federation (RFFM) sync — designed and led end-to-end.",
        metric="−6 h/week saved  ·  −15–20% errors  ·  17 modules",
        chips=[("Python", "python"), ("Django", "django"), ("Docker", "docker"), ("AWS", "amazonwebservices")],
    ),
    dict(
        file="archtrace", title="ArchTrace Auditor", glyph="typescript",
        tag="AI · DEV TOOLS", tag_c=VIOLET, a=VIOLET, b=PINK,
        desc="Audits what AI agents changed before you accept it: deterministic rules, your repo's "
             "own rules and a validated BYOK LLM, with diff review and a traceable report.",
        metric="18 risk categories  ·  RAG over repo rules  ·  CI-ready",
        chips=[("TypeScript", "typescript"), ("Next.js", "nextdotjs"), ("Ollama", "ollama"), ("tree-sitter", None)],
    ),
    dict(
        file="albertitos", title="Albertitos · Maisa", glyph="anthropic",
        tag="HACKSPAIN '26 · LIVE", tag_c=PINK, a=PINK, b=AMBER,
        desc="AI accounts-payable decisioning: the LLM extracts, versioned rules decide PAY / REJECT / "
             "ESCALATE — every decision traceable and replayable. I built the web console.",
        metric="540 invoices decided  ·  718 tests  ·  0 pending",
        chips=[("Next.js", "nextdotjs"), ("React", "react"), ("Tailwind", "tailwindcss"), ("Python", "python")],
    ),
    dict(
        file="madrid", title="Madrid Commercial Intel", glyph="streamlit",
        tag="LIVE DEMO", tag_c=CYAN, a=CYAN, b=VIOLET,
        desc="Finds the best commercial premises in Madrid from public open data and a custom scoring "
             "engine: demographics, competition, foot traffic and tourism on live maps.",
        metric="custom scoring engine  ·  heatmaps  ·  GitHub Pages",
        chips=[("Python", "python"), ("pandas", "pandas"), ("Streamlit", "streamlit"), ("Leaflet", None)],
    ),
    dict(
        file="betech", title="BeTech Hackathon", glyph="huggingface",
        tag="1ST PRIZE · 2025", tag_c=AMBER, a=AMBER, b=PINK,
        desc="Estimates diabetes probability from noisy, unstructured clinical notes with an ensemble "
             "of clinical NLP models such as BioClinicalBERT. With Roche, BEST Madrid & UPM.",
        metric="clinical NLP  ·  model ensemble  ·  early decision support",
        chips=[("Python", "python"), ("Hugging Face", "huggingface"), ("scikit-learn", "scikitlearn")],
    ),
    dict(
        file="indesia", title="IndesIA Hackathon", glyph="openai",
        tag="1ST PRIZE · 2025", tag_c=AMBER, a=AMBER, b=CYAN,
        desc="Reads corrected engineering PDFs, extracts the marked regions with PyMuPDF + OpenCV and "
             "reviews them with GPT-4o. Built with Técnicas Reunidas & Bravent.",
        metric="PDF vision pipeline  ·  GPT-4o review  ·  Dockerised API",
        chips=[("React", "react"), ("TypeScript", "typescript"), ("FastAPI", "fastapi"), ("OpenAI", "openai")],
    ),
]


def chip(x: float, y: float, label: str, slug: str | None, h: float = 30) -> tuple[str, float]:
    fs = 14
    pad = 12
    iw = 15 if slug else 0
    gap = 8 if slug else 0
    w = pad + iw + gap + measure(label, "jb400", fs) + pad
    out = (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="#ffffff" '
           f'fill-opacity=".045" stroke="#ffffff" stroke-opacity=".08"/>')
    if slug:
        out += icon(slug, x + pad, y + (h - iw) / 2, iw)
    out += (f'<text x="{x + pad + iw + gap:.1f}" y="{y + h / 2 + 5}" class="jb w4" font-size="{fs}" '
            f'fill="{MUTED}">{esc(label)}</text>')
    return out, w


def project_cards() -> None:
    W, H = 600, 350
    for i, p in enumerate(PROJECTS):
        a, b = p["a"], p["b"]
        tag_fs, tag_ls = 12.5, 1.3
        tw = spaced_width(p["tag"], "jb700", tag_fs, tag_ls) + 26
        tx = W - 30 - tw
        desc = wrap(p["desc"], "sg400", 18.5, W - 64)
        assert len(desc) <= 3, (p["file"], desc)
        parts = [
            f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="{PANEL}"/>',
            f'<g clip-path="url(#cl)"><circle class="orb" cx="{W - 40}" cy="30" r="190" fill="url(#orb)"/>'
            f'<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gm)"/></g>',
            f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" stroke="url(#bd)" stroke-width="1.6"/>',
            # icon tile
            f'<rect x="30" y="30" width="58" height="58" rx="16" fill="url(#tile)"/>',
            f'<rect x="30.5" y="30.5" width="57" height="57" rx="15.5" stroke="#fff" stroke-opacity=".18"/>',
            icon(p["glyph"], 44, 44, 30, "#ffffff"),
            # tag
            f'<rect x="{tx:.1f}" y="44" width="{tw:.1f}" height="30" rx="15" fill="{p["tag_c"]}" fill-opacity=".1" '
            f'stroke="{p["tag_c"]}" stroke-opacity=".45"/>',
            f'<text x="{tx + 13:.1f}" y="64" class="jb w7" font-size="{tag_fs}" letter-spacing="{tag_ls}" '
            f'fill="{p["tag_c"]}">{esc(p["tag"])}</text>',
            f'<text x="30" y="136" class="sg w7" font-size="32" letter-spacing="-.6" fill="{TEXT}">{esc(p["title"])}</text>',
        ]
        for j, line in enumerate(desc):
            parts.append(f'<text x="30" y="{170 + j * 26}" class="sg w4" font-size="18.5" fill="{MUTED}">{esc(line)}</text>')
        parts.append(f'<rect x="30" y="{254}" width="3" height="20" rx="1.5" fill="url(#tile)"/>'
                     f'<text x="44" y="269" class="jb w7" font-size="14.5" fill="{a}">{esc(p["metric"])}</text>')
        cx = 30
        for label, slug in p["chips"]:
            svg, w = chip(cx, 294, label, slug)
            parts.append(svg)
            cx += w + 8
        assert cx < W - 76, (p["file"], cx)
        # arrow
        parts.append(f'<g class="arrow"><circle cx="{W - 46}" cy="309" r="17" fill="#ffffff" fill-opacity=".05" '
                     f'stroke="#ffffff" stroke-opacity=".12"/><path d="M{W - 52} 315 l12 -12 M{W - 49} 303 h9 v9" '
                     f'stroke="{TEXT}" stroke-width="2" stroke-linecap="round"/></g>')
        defs = f"""
<clipPath id="cl"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24"/></clipPath>
<radialGradient id="orb"><stop offset="0" stop-color="{a}" stop-opacity=".22"/><stop offset="1" stop-color="{a}" stop-opacity="0"/></radialGradient>
<linearGradient id="tile" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>
<linearGradient id="bd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}" stop-opacity=".9"/><stop offset=".3" stop-color="{STROKE}"/><stop offset=".7" stop-color="{STROKE}"/><stop offset="1" stop-color="{b}" stop-opacity=".7"/>{ROTATE_BORDER.format(dur=8 + i)}</linearGradient>
<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" stroke="#fff" stroke-opacity=".035"/></pattern>
<radialGradient id="gf" cx="1" cy="0" r="1"><stop offset="0" stop-color="#fff"/><stop offset=".8" stop-color="#000"/></radialGradient>
<mask id="gm"><rect width="{W}" height="{H}" fill="url(#gf)"/></mask>
"""
        css = (".orb{animation:ob 6s ease-in-out infinite;transform-origin:560px 30px}"
               "@keyframes ob{50%{transform:scale(1.25);opacity:.6}}"
               f".arrow{{animation:ar 3s ease-in-out infinite;animation-delay:{i * .4:.1f}s}}"
               "@keyframes ar{0%,70%,100%{transform:none}80%{transform:translate(4px,-4px)}}")
        save(f"projects/{p['file']}.svg",
             document("".join(parts), W, H, ["sg400", "sg700", "jb400", "jb700"], css, p["title"], defs))


# ── 6. data-engineering pipeline ───────────────────────────────────────────

STAGES = [
    ("01 · STREAM", "Apache Kafka", "apachekafka", "KRaft cluster · real-time", "practica-kafka-etsit", CYAN),
    ("02 · PROCESS", "Apache Spark", "apachespark", "PySpark + Scala · ML", "flight-prediction", AMBER),
    ("03 · ORCHESTRATE", "Airflow", "apacheairflow", "scheduled, dockerised DAGs", "flight-prediction", VIOLET),
    ("04 · OBSERVE", "Kubernetes", "kubernetes", "Prometheus + Grafana", "k8s-iot-monitoring", PINK),
]


def pipeline() -> None:
    W, H = 1200, 420
    bw, bh, by = 236, 196, 70
    gap = (W - 60 - 4 * bw) / 3
    xs = [30 + k * (bw + gap) for k in range(4)]
    cy = by + bh / 2
    flow = f"M10 {cy} H{W - 10}"
    parts = [
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="{BG1}"/>',
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="url(#dots)"/>',
        f'<text x="30" y="44" class="jb w7" font-size="13" letter-spacing="2" fill="{DIM}">DATA FLOW · END-TO-END PRACTICE PROJECTS @ ETSIT-UPM</text>',
        f'<path d="{flow}" stroke="{STROKE}" stroke-width="2"/>',
        f'<path class="flow" d="{flow}" stroke="url(#fl)" stroke-width="2.5" stroke-dasharray="6 14"/>',
    ]
    for k in range(9):
        col = [CYAN, AMBER, VIOLET, PINK][k % 4]
        dur = 5.5
        parts.append(f'<circle r="4.5" fill="{col}" filter="url(#glow)">'
                     f'<animateMotion path="{flow}" dur="{dur}s" begin="{-k * dur / 9:.2f}s" repeatCount="indefinite"/></circle>')
    for k, (stage, name, slug, note, repo, col) in enumerate(STAGES):
        x = xs[k]
        parts.append(
            f'<g><rect x="{x:.1f}" y="{by}" width="{bw}" height="{bh}" rx="20" fill="{PANEL}"/>'
            f'<rect x="{x:.1f}" y="{by}" width="{bw}" height="{bh}" rx="20" fill="url(#st{k})"/>'
            f'<rect x="{x:.1f}" y="{by}" width="{bw}" height="{bh}" rx="20" stroke="{col}" stroke-opacity=".5" stroke-width="1.5">'
            f'<animate attributeName="stroke-opacity" values=".25;1;.25" dur="5.5s" begin="{k * 5.5 / 4 * 0.98:.2f}s" repeatCount="indefinite"/></rect>'
            f'<rect x="{x + 22:.1f}" y="{by + 22}" width="50" height="50" rx="14" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-opacity=".4"/>'
            f'{icon(slug, x + 33, by + 33, 28, col)}'
            f'<text x="{x + 22:.1f}" y="{by + 104}" class="jb w7" font-size="12.5" letter-spacing="1.5" fill="{col}">{esc(stage)}</text>'
            f'<text x="{x + 22:.1f}" y="{by + 134}" class="sg w7" font-size="25" letter-spacing="-.4" fill="{TEXT}">{esc(name)}</text>'
            f'<text x="{x + 22:.1f}" y="{by + 162}" class="sg w4" font-size="16" fill="{MUTED}">{esc(note)}</text>'
            f'<text x="{x + 22:.1f}" y="{by + 183}" class="jb w4" font-size="12.5" fill="{DIM}">{esc("↳ " + repo)}</text></g>')
    # infra band
    infra = [("Docker", "docker"), ("Kubernetes", "kubernetes"), ("Prometheus", "prometheus"),
             ("Grafana", "grafana"), ("Spark MLlib", "apachespark"), ("MongoDB", "mongodb"), ("Jupyter", "jupyter")]
    band_y = 300
    parts.append(f'<rect x="30" y="{band_y}" width="{W - 60}" height="90" rx="18" fill="#ffffff" fill-opacity=".025" stroke="{STROKE}" stroke-dasharray="4 6"/>'
                 f'<text x="52" y="{band_y + 34}" class="jb w7" font-size="12.5" letter-spacing="2" fill="{DIM}">RUNS ON</text>')
    cx = 52
    for label, slug in infra:
        svg, w = chip(cx, band_y + 46, label, slug)
        parts.append(svg)
        cx += w + 10
    assert cx < W - 40, cx
    defs = [f'<filter id="glow" x="-300%" y="-300%" width="700%" height="700%"><feGaussianBlur stdDeviation="4" result="b"/>'
            f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
            f'<linearGradient id="fl" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{CYAN}"/><stop offset=".35" stop-color="{AMBER}"/>'
            f'<stop offset=".65" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>',
            f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#fff" fill-opacity=".05"/></pattern>']
    for k, (*_, col) in enumerate(STAGES):
        defs.append(f'<linearGradient id="st{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{col}" stop-opacity=".09"/>'
                    f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></linearGradient>')
    css = ".flow{animation:fw 1.2s linear infinite}@keyframes fw{to{stroke-dashoffset:-20}}"
    save("pipeline.svg", document("".join(parts), W, H, ["sg400", "sg700", "jb400", "jb700"], css,
                                  "Data engineering lab: Kafka → Spark → Airflow → Kubernetes", "".join(defs)))


# ── 7. tech-stack marquee ──────────────────────────────────────────────────

STACK = [
    [("Python", "python"), ("SQL", "postgresql"), ("pandas", "pandas"), ("NumPy", "numpy"),
     ("scikit-learn", "scikitlearn"), ("Hugging Face", "huggingface"), ("Jupyter", "jupyter"),
     ("Apache Spark", "apachespark"), ("Apache Kafka", "apachekafka"), ("Airflow", "apacheairflow"),
     ("MongoDB", "mongodb"), ("Streamlit", "streamlit"), ("OpenAI", "openai"), ("Ollama", "ollama")],
    [("TypeScript", "typescript"), ("JavaScript", "javascript"), ("React", "react"), ("Next.js", "nextdotjs"),
     ("Tailwind CSS", "tailwindcss"), ("Django", "django"), ("FastAPI", "fastapi"), ("Docker", "docker"),
     ("Kubernetes", "kubernetes"), ("AWS", "amazonwebservices"), ("Prometheus", "prometheus"),
     ("Grafana", "grafana"), ("Git", "git"), ("GitHub Actions", "githubactions"), ("Vercel", "vercel")],
]


def stack() -> None:
    W, H = 1200, 228
    ch, fs = 58, 20
    rows_svg = []
    css = []
    for r, items in enumerate(STACK):
        y = 28 + r * (ch + 26)
        pieces, x = [], 0.0
        for label, slug in items:
            w = 18 + 26 + 12 + measure(label, "sg500", fs) + 22
            col = icon_color(slug)
            pieces.append(
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{ch}" rx="18" fill="{PANEL}" stroke="{STROKE}"/>'
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{ch}" rx="18" fill="{col}" fill-opacity=".05"/>'
                f'{icon(slug, x + 18, y + (ch - 26) / 2, 26)}'
                f'<text x="{x + 56:.1f}" y="{y + ch / 2 + 7}" class="sg w5" font-size="{fs}" fill="{TEXT}">{esc(label)}</text>')
            x += w + 14
        L = x
        assert L > W, "row must be wider than the canvas for a seamless loop"
        group = "".join(pieces)
        dur = L / 42
        rows_svg.append(f'<g class="m{r}"><g>{group}</g><g transform="translate({L:.1f} 0)">{group}</g></g>')
        if r == 0:
            css.append(f".m0{{animation:m0 {dur:.1f}s linear infinite}}@keyframes m0{{to{{transform:translateX(-{L:.1f}px)}}}}")
        else:
            css.append(f".m1{{animation:m1 {dur:.1f}s linear infinite;transform:translateX(-{L:.1f}px)}}"
                       f"@keyframes m1{{from{{transform:translateX(-{L:.1f}px)}}to{{transform:translateX(0)}}}}")
    defs = (f'<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#000"/><stop offset=".09" stop-color="#fff"/>'
            f'<stop offset=".91" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
            f'<mask id="fade"><rect width="{W}" height="{H}" fill="url(#edge)"/></mask>')
    body = f'<g mask="url(#fade)">{"".join(rows_svg)}</g>'
    save("stack.svg", document(body, W, H, ["sg500"], "".join(css), "Tech stack", defs))


# ── 8. awards timeline ─────────────────────────────────────────────────────

AWARDS = [
    ("2020", "EdwingEd Youth Entrepreneurship", "1st Prize · presented by the Mayor of Madrid", True),
    ("2023", "Maestro Miguel Literature Award", "1st Prize · Villanueva del Pardillo", True),
    ("2024", "Youth IGF Spain", "1st Prize · ETSIT-UPM, DigitalES, AdigitalES", True),
    ("2025", "BeTech Hackathon", "1st Prize · UPM, BEST Madrid & Roche", True),
    ("2025", "IndesIA Hackathon", "1st Prize · Técnicas Reunidas & Bravent", True),
    ("2026", "ActúaUPM", "23rd Business Creation Competition · advancing", False),
]


def star(cx: float, cy: float, r: float, fill: str) -> str:
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45
        ang = -math.pi / 2 + k * math.pi / 5
        pts.append(f"{cx + rr * math.cos(ang):.1f},{cy + rr * math.sin(ang):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


def awards() -> None:
    W, H = 1200, 470
    axis = 228
    n = len(AWARDS)
    step = (W - 120) / (n - 1)
    xs = [60 + k * step for k in range(n)]
    cw = 196
    draw = 2.4
    parts = [
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="{BG1}"/>',
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="24" fill="url(#halo)"/>',
        f'<path d="M30 {axis}H{W - 30}" stroke="{STROKE}" stroke-width="2"/>',
        f'<path d="M30 {axis}H{W - 30}" stroke="url(#ax)" stroke-width="3" stroke-linecap="round" '
        f'stroke-dasharray="{W - 60}" stroke-dashoffset="{W - 60}"><animate attributeName="stroke-dashoffset" to="0" '
        f'dur="{draw}s" begin=".2s" fill="freeze" calcMode="spline" keySplines=".4 0 .2 1" keyTimes="0;1"/></path>',
        f'<circle r="5" fill="#fff" filter="url(#glow)" opacity="0"><set attributeName="opacity" to="1" begin="{draw + .3}s" fill="freeze"/>'
        f'<animateMotion path="M30 {axis}H{W - 30}" dur="6s" begin="{draw + .3}s" repeatCount="indefinite"/></circle>',
    ]
    for k, (year, title, org, won) in enumerate(AWARDS):
        x = xs[k]
        up = k % 2 == 0
        t = 0.2 + draw * (x - 30) / (W - 60)
        col = AMBER if won else VIOLET
        tl = wrap(title, "sg700", 19, cw - 8)
        ol = wrap(org, "sg400", 14.5, cw - 8)
        block_h = 22 + len(tl) * 23 + 6 + len(ol) * 19
        y0 = axis - 40 - block_h if up else axis + 40
        x_text = min(max(x - cw / 2, 30), W - 30 - cw)
        anchor = x_text
        g = [f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{t:.2f}s" dur=".5s" fill="freeze"/>'
             f'<animateTransform attributeName="transform" type="translate" from="0 {14 if up else -14}" to="0 0" '
             f'begin="{t:.2f}s" dur=".7s" fill="freeze" calcMode="spline" keySplines=".2 .8 .2 1" keyTimes="0;1"/>']
        g.append(f'<path d="M{x:.1f} {axis + (-14 if up else 14)} V{(y0 + block_h + 10) if up else (y0 - 10)}" '
                 f'stroke="{col}" stroke-opacity=".45" stroke-dasharray="3 4"/>')
        yy = y0 + 16
        g.append(f'<text x="{anchor:.1f}" y="{yy:.1f}" class="jb w7" font-size="15" letter-spacing="1.5" fill="{col}">{year}</text>')
        yy += 26
        for line in tl:
            g.append(f'<text x="{anchor:.1f}" y="{yy:.1f}" class="sg w7" font-size="19" fill="{TEXT}">{esc(line)}</text>')
            yy += 23
        yy += 4
        for line in ol:
            g.append(f'<text x="{anchor:.1f}" y="{yy:.1f}" class="sg w4" font-size="14.5" fill="{MUTED}">{esc(line)}</text>')
            yy += 19
        g.append("</g>")
        parts.extend(g)
        # node
        node = [f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>',
                f'<circle cx="{x:.1f}" cy="{axis}" r="13" fill="{BG1}" stroke="{col}" stroke-width="2"/>']
        if won:
            node.append(star(x, axis, 7.5, col))
        else:
            node.append(f'<circle cx="{x:.1f}" cy="{axis}" r="4.5" fill="{col}"/>')
        node.append(f'<circle cx="{x:.1f}" cy="{axis}" r="13" fill="none" stroke="{col}" stroke-width="1.5">'
                    f'<animate attributeName="r" values="13;30" dur="{2.6 if won else 1.6}s" begin="{t:.2f}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values=".7;0" dur="{2.6 if won else 1.6}s" begin="{t:.2f}s" repeatCount="indefinite"/></circle></g>')
        parts.extend(node)
    # legend
    parts.append(f'{star(42, H - 28, 6, AMBER)}<text x="56" y="{H - 23}" class="jb w4" font-size="13" fill="{MUTED}">first prize</text>'
                 f'<circle cx="166" cy="{H - 28}" r="4.5" fill="{VIOLET}"/><text x="178" y="{H - 23}" class="jb w4" font-size="13" fill="{MUTED}">in progress</text>')
    defs = (f'<linearGradient id="ax" x1="30" y1="0" x2="{W - 30}" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{CYAN}"/><stop offset=".6" stop-color="{AMBER}"/>'
            f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient>'
            f'<radialGradient id="halo" cx=".5" cy=".5" r=".6"><stop offset="0" stop-color="{AMBER}" stop-opacity=".07"/>'
            f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>'
            f'<filter id="glow" x="-300%" y="-300%" width="700%" height="700%"><feGaussianBlur stdDeviation="4" result="b"/>'
            f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    save("awards.svg", document("".join(parts), W, H, ["sg400", "sg700", "jb400", "jb700"], "",
                                "Awards and recognition 2020-2026", defs))


# ── 9. footer ──────────────────────────────────────────────────────────────


def footer() -> None:
    W, H = 1200, 190
    waves = []
    for k, (col, amp, wl, y, dur, op) in enumerate([
        (CYAN, 16, 300, 120, 9, .55), (VIOLET, 22, 400, 128, 13, .45), (PINK, 12, 240, 136, 7, .4)]):
        pts = []
        x = -wl
        d = f"M{-wl} {y}"
        while x < W + wl:
            d += f" q{wl / 4} {-amp} {wl / 2} 0 t{wl / 2} 0"
            x += wl
        waves.append(f'<path class="w{k}" d="{d}" stroke="{col}" stroke-opacity="{op}" stroke-width="2"/>')
        waves.append(f"<style>.w{k}{{animation:wv{k} {dur}s linear infinite}}@keyframes wv{k}{{to{{transform:translateX({wl}px)}}}}</style>")
    msg = "Thanks for stopping by — let's build something with data."
    body = (f'<g mask="url(#fade)">{"".join(waves)}</g>'
            f'<text x="{W / 2}" y="60" text-anchor="middle" class="sg w5" font-size="26" fill="{TEXT}">{esc(msg)}</text>'
            f'<text x="{W / 2}" y="{H - 12}" text-anchor="middle" class="jb w4" font-size="13" fill="{DIM}">'
            f'ALEJANDRO CUEVAS CID · MADRID · 2026</text>')
    defs = (f'<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#000"/><stop offset=".2" stop-color="#fff"/>'
            f'<stop offset=".8" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
            f'<mask id="fade"><rect width="{W}" height="{H}" fill="url(#edge)"/></mask>')
    save_themed("footer.svg", document(body, W, H, ["sg500", "jb400"], "", "Thanks for visiting", defs))


if __name__ == "__main__":
    print("building assets/")
    header()
    section_titles()
    buttons()
    terminal()
    project_cards()
    pipeline()
    stack()
    awards()
    footer()
