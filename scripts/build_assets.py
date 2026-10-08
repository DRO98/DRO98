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
    W, H = 1200, 420
    rnd = random.Random(98)

    # data-graph constellation on the right
    nodes = []
    while len(nodes) < 22:
        p = (rnd.uniform(760, 1150), rnd.uniform(50, 370))
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
<g transform="translate(0 -60)">{name}{"".join(typer)}{"".join(meta_svg)}</g>
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="27.5" stroke="url(#rim)" stroke-width="1.5"/>
"""
    save("header.svg", document(body, W, H, ["sg700", "jb400", "jb700"], css,
                                "Alejandro Cuevas Cid — Data Systems Engineer", defs))


# ── 2. section titles ──────────────────────────────────────────────────────

SECTIONS = [
    ("01", "Tech stack", "tools I ship with"),
    ("02", "Recognition", "2020 → 2026"),
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

ENVELOPE = ('<g stroke="#fff" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round" fill="none">'
            '<rect x="{x}" y="{y}" width="30" height="22" rx="5"/><path d="M{x1} {y1} l11.5 8.5 l11.5 -8.5"/></g>')

BUTTONS = [
    # file, label, handle, colour a, colour b
    ("linkedin", "LinkedIn", "in/alejandro-cuevas-cid", "#0A66C2", "#38bdf8"),
    ("email", "Email", "alejandrocuevascm@gmail.com", PINK, VIOLET),
]


def buttons() -> None:
    W, H = 440, 104
    r = H / 2 - 2
    for i, (slug, label, handle, a, b) in enumerate(BUTTONS):
        cx, cy = 54, H / 2
        if slug == "linkedin":
            glyph = (f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" class="sg w7" font-size="30" '
                     f'letter-spacing="-.5" fill="#fff">in</text>')
        else:
            glyph = ENVELOPE.format(x=cx - 15, y=cy - 11, x1=cx - 11.5, y1=cy - 5)
        pill = f'x="2" y="2" width="{W - 4}" height="{H - 4}" rx="{r}"'
        body = f"""
<rect {pill} fill="url(#bg)"/>
<rect {pill} fill="url(#tint)"/>
<g clip-path="url(#c)"><rect class="shine" x="-140" y="-20" width="80" height="{H + 40}" fill="url(#sh)"/></g>
<rect {pill} stroke="#ffffff" stroke-opacity=".09" stroke-width="1.5"/>
<rect {pill} pathLength="100" stroke="url(#cm)" stroke-width="5" stroke-linecap="round" stroke-dasharray="14 86" filter="url(#blur)" opacity=".8">
<animate attributeName="stroke-dashoffset" from="{100 + i * 50}" to="{i * 50}" dur="4s" repeatCount="indefinite"/></rect>
<rect {pill} pathLength="100" stroke="url(#cm)" stroke-width="2" stroke-linecap="round" stroke-dasharray="14 86">
<animate attributeName="stroke-dashoffset" from="{100 + i * 50}" to="{i * 50}" dur="4s" repeatCount="indefinite"/></rect>
<circle cx="{cx}" cy="{cy}" r="32" fill="none" stroke="{b}" stroke-width="1.5">
<animate attributeName="r" values="32;46" dur="2.4s" repeatCount="indefinite"/>
<animate attributeName="opacity" values=".6;0" dur="2.4s" repeatCount="indefinite"/></circle>
<circle cx="{cx}" cy="{cy}" r="32" fill="url(#disc)"/>
<circle cx="{cx}" cy="{cy}" r="31.5" stroke="#fff" stroke-opacity=".25"/>
{glyph}
<text x="104" y="{cy - 3}" class="sg w7" font-size="28" letter-spacing="-.4" fill="{TEXT}">{esc(label)}</text>
<text x="105" y="{cy + 23}" class="jb w4" font-size="14.5" fill="{MUTED}">{esc(handle)}</text>
<g class="arrow"><circle cx="{W - 46}" cy="{cy}" r="22" fill="#ffffff" fill-opacity=".05" stroke="#ffffff" stroke-opacity=".14"/>
<path d="M{W - 52} {cy + 6} l12 -12 M{W - 49} {cy - 6} h9 v9" stroke="{TEXT}" stroke-width="2.2" stroke-linecap="round" fill="none"/></g>
"""
        assert 105 + measure(handle, "jb400", 14.5) < W - 76, slug
        defs = f"""
<clipPath id="c"><rect {pill}/></clipPath>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#141831"/><stop offset="1" stop-color="{BG0}"/></linearGradient>
<radialGradient id="tint" cx="0" cy=".5" r=".75"><stop offset="0" stop-color="{a}" stop-opacity=".35"/><stop offset="1" stop-color="{a}" stop-opacity="0"/></radialGradient>
<linearGradient id="disc" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>
<linearGradient id="cm" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>
<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<filter id="blur" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
"""
        css = (f".shine{{animation:sh 5s ease-in-out {i * 1.2:.1f}s infinite}}"
               "@keyframes sh{0%,50%{transform:skewX(-20deg) translateX(0)}100%{transform:skewX(-20deg) translateX(720px)}}"
               f".arrow{{animation:ar 3s ease-in-out {i * .5:.1f}s infinite}}"
               "@keyframes ar{0%,70%,100%{transform:none}82%{transform:translateX(5px)}}")
        save(f"buttons/{slug}.svg", document(body, W, H, ["sg700", "jb400"], css, f"{label} — {handle}", defs))


# ── 4. tech-stack marquee ──────────────────────────────────────────────────

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


# ── 5. awards timeline ─────────────────────────────────────────────────────

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


# ── 6. footer ──────────────────────────────────────────────────────────────


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
    stack()
    awards()
    footer()
