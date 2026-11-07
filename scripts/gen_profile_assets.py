#!/usr/bin/env python3
"""Génère contributions.svg et stats.svg (DA du portfolio : sombre, accent vert). Texte converti en tracés.

Sources de données, sans clé d'API ni service tiers :
  - le calendrier public de contributions (https://github.com/users/<user>/contributions)
  - l'API REST publique pour les dépôts et les langages (GITHUB_TOKEN utilisé s'il existe, pour le quota)

Usage : python3 scripts/gen_profile_assets.py [dossier_sortie] [--sample]
Dépendances : fonttools et brotli (pip install fonttools brotli). Les polices viennent de scripts/fonts/.
"""
import datetime as dt, json, os, random, re, sys, urllib.request
from html import unescape
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textpath import Font

HERE = os.path.dirname(os.path.abspath(__file__))
USER = os.environ.get("GITHUB_REPOSITORY_OWNER", "YannLf3")
TOKEN = os.environ.get("GITHUB_TOKEN")

GROUND, SURFACE, CARD = "#090b10", "#11141a", "#13161d"
TEXT, MUTED = "#f3f2ed", "#95989f"
ACCENT, ACCENT2 = "#00f8a8", "#00d3e5"
LANG_COLORS = ["#00f8a8", "#00d3e5", "#7cf2c8", "#5aa9e6", "#c8f7e4", "#ffae5d", "#4a5160"]
FONTS = {
    "Fraunces": "fraunces-400.woff2",
    "Inter": "inter-400.woff2",
    "JetBrains Mono": "jetbrains-mono-400.woff2",
}
FONTOBJ = {k: Font(os.path.join(HERE, "fonts", v)) for k, v in FONTS.items()}


# ------------------------------------------------------------------ données
def get(url, accept=None):
    req = urllib.request.Request(url, headers={"User-Agent": f"{USER}-profile-readme"})
    if accept:
        req.add_header("Accept", accept)
    if TOKEN and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def load_calendar():
    page = get(f"https://github.com/users/{USER}/contributions")
    tips = {i: t for i, t in re.findall(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', page)}
    days = []
    for tag in re.findall(r"<td\b[^>]*>", page):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
        if "data-date" not in a:
            continue
        m = re.search(r"(\d+)\s+contribution", unescape(tips.get(a.get("id", ""), "")))
        days.append((dt.date.fromisoformat(a["data-date"]), int(m.group(1)) if m else 0))
    if not days:
        raise RuntimeError("calendrier de contributions introuvable")
    return sorted(days)


def load_repos():
    repos = json.loads(get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed"))
    repos = [r for r in repos if not r["fork"] and not r["private"]]
    langs = {}
    for r in repos:
        try:
            for k, v in json.loads(get(r["languages_url"])).items():
                langs[k] = langs.get(k, 0) + v
        except Exception as e:  # un dépôt en échec ne doit pas bloquer le reste
            print("langages ignorés pour", r["name"], e, file=sys.stderr)
    return len(repos), sum(r["stargazers_count"] for r in repos), langs


def sample():
    rnd = random.Random(7)
    end = dt.date.today()
    days = []
    d = end - dt.timedelta(days=364)
    while d <= end:
        days.append((d, 0 if rnd.random() < 0.58 else rnd.choice([1, 1, 2, 3, 5, 8, 12])))
        d += dt.timedelta(days=1)
    return days, 21, 4, {"JavaScript": 52000, "PHP": 41000, "CSS": 22000, "HTML": 18000, "Python": 9000, "Blade": 3000}


# ------------------------------------------------------------------ rendu
class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.b = w, h, []

    def add(self, s):
        self.b.append(s)

    def text(self, x, y, s, fam, size, fill, anchor="start", ls=0, opacity=1, upper=False, extra=""):
        s = s.upper() if upper else s
        d = FONTOBJ[fam].path(s, x, y, size, ls, anchor)
        self.add(f'<g fill="{fill}" opacity="{opacity}" {extra}><path d="{d}"/></g>')

    def save(self, path, title, desc, defs=""):
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc><defs>{defs}</defs>'
            + "".join(self.b) + "</svg>"
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(os.path.basename(path), f"{len(svg)/1024:.0f} Ko")


def frame(s, title):
    W, H = s.w, s.h
    s.add(f'<g clip-path="url(#panel)"><rect width="{W}" height="{H}" fill="{GROUND}"/>')
    s.add(f'<rect width="{W}" height="{H}" fill="url(#dots)"/><rect width="{W}" height="{H}" fill="url(#glow)"/>')
    s.add(f'<rect width="{W}" height="46" fill="{SURFACE}"/><line x1="0" y1="46" x2="{W}" y2="46" stroke="#fff" stroke-opacity=".09"/>')
    for cx, col in ((30, "#fb2c36"), (52, "#edb200"), (74, "#00c758")):
        s.add(f'<circle cx="{cx}" cy="23" r="6" fill="{col}" opacity=".8"/>')
    s.text(104, 28, title, "JetBrains Mono", 13, MUTED)
    s.add("</g>")
    s.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="#fff" stroke-opacity=".18"/>')


def common_defs(w, h):
    return (
        f'<radialGradient id="glow" cx="85%" cy="0%" r="70%"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".13"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>'
        '<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#fff" opacity=".06"/></pattern>'
        f'<clipPath id="panel"><rect width="{w}" height="{h}" rx="20"/></clipPath>'
    )


def levels(days):
    nz = sorted(c for _, c in days if c)
    if not nz:
        return lambda c: 0
    q = [nz[int(len(nz) * p)] for p in (0.25, 0.5, 0.75)]

    def level(c):
        if c == 0:
            return 0
        if c <= q[0]:
            return 1
        if c <= q[1]:
            return 2
        if c <= q[2]:
            return 3
        return 4

    return level


FR_MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
FR_DAYS = ["", "Lun", "", "Mer", "", "Ven", ""]
OPAC = [None, 0.26, 0.50, 0.76, 1.0]


def contributions_svg(days, out):
    W, H = 1200, 340
    s = Svg(W, H)
    frame(s, f"{USER.lower()}@github:~ (activité)")
    total = sum(c for _, c in days)
    s.text(40, 112, f"{total:,}".replace(",", " "), "Fraunces", 56, ACCENT)
    s.text(40 + FONTOBJ["Fraunces"].width(f"{total:,}".replace(",", " "), 56) + 18, 108, "contributions sur les 12 derniers mois", "Inter", 17, TEXT, opacity=0.85)
    lvl = levels(days)
    first = days[0][0]
    first_sun = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    x0, y0, cell, pitch = 76, 168, 16, 20
    last_month = None
    for i, lab in enumerate(FR_DAYS):
        if lab:
            s.text(x0 - 14, y0 + i * pitch + 12, lab, "JetBrains Mono", 10, MUTED, anchor="end")
    today = days[-1][0]
    for d, c in days:
        row = (d.weekday() + 1) % 7
        col = (d - first_sun).days // 7
        x, y = x0 + col * pitch, y0 + row * pitch
        if row == 0 and (last_month != d.month) and x < x0 + 52 * pitch - 30:
            s.text(x, y0 - 12, FR_MONTHS[d.month - 1], "JetBrains Mono", 10, MUTED)
            last_month = d.month
        lv = lvl(c)
        if lv == 0:
            s.add(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="#fff" fill-opacity=".055"/>')
        else:
            delay = round(col * 0.035 + row * 0.02, 2)
            dur = round(delay + 0.5, 2)
            s.add(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{ACCENT}" fill-opacity="{OPAC[lv]}">'
                f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{delay / dur:.3f};1" dur="{dur}s" fill="freeze"/>'
                f"<title>{c} contribution{'s' if c > 1 else ''} le {d.day}/{d.month:02d}/{d.year}</title></rect>"
            )
        if d == today:
            s.add(
                f'<rect x="{x - 2}" y="{y - 2}" width="{cell + 4}" height="{cell + 4}" rx="6" fill="none" stroke="{ACCENT}" stroke-width="1.5">'
                f'<animate attributeName="opacity" values="1;.2;1" dur="2.4s" repeatCount="indefinite"/></rect>'
            )
    # légende
    lx = W - 40 - 5 * pitch - 70
    s.text(lx - 10, 112, "Moins", "JetBrains Mono", 10, MUTED, anchor="end")
    for i in range(5):
        op = ".055" if i == 0 else OPAC[i]
        fill = "#fff" if i == 0 else ACCENT
        s.add(f'<rect x="{lx + i * pitch}" y="100" width="{cell}" height="{cell}" rx="4" fill="{fill}" fill-opacity="{op}"/>')
    s.text(lx + 5 * pitch + 6, 112, "Plus", "JetBrains Mono", 10, MUTED)
    s.save(out, "Contributions GitHub des 12 derniers mois", f"Calendrier de contributions : {total} contributions sur les 12 derniers mois.", common_defs(W, H))


def longest_streak(days):
    best = cur = 0
    for _, c in days:
        cur = cur + 1 if c else 0
        best = max(best, cur)
    return best


def stats_svg(days, n_repos, stars, langs, out):
    W, H = 1200, 330
    s = Svg(W, H)
    frame(s, f"{USER.lower()}@github:~ (stats)")
    total = sum(c for _, c in days)
    tiles = [
        ("Contributions", f"{total:,}".replace(",", " "), "12 derniers mois"),
        ("Jours actifs", str(sum(1 for _, c in days if c)), "sur 365 jours"),
        ("Série max", str(longest_streak(days)), "jours d'affilée"),
        ("Dépôts publics", str(n_repos), "hors forks"),
        ("Étoiles reçues", str(stars), "sur mes dépôts"),
    ]
    tw, gap, x, y = 216, 14, 32, 74
    for label, val, sub in tiles:
        s.add(f'<rect x="{x}" y="{y}" width="{tw}" height="104" rx="14" fill="{CARD}" stroke="#fff" stroke-opacity=".12"/>')
        s.add(f'<rect x="{x}" y="{y + 18}" width="3" height="68" rx="1.5" fill="{ACCENT}" opacity=".9"/>')
        s.text(x + 24, y + 30, label, "JetBrains Mono", 10, MUTED, ls=0.14, upper=True)
        s.text(x + 24, y + 70, val, "Fraunces", 40, TEXT)
        s.text(x + 24, y + 92, sub, "Inter", 12, MUTED)
        x += tw + gap
    # langages
    s.text(32, 220, "Langages les plus utilisés", "JetBrains Mono", 11, MUTED, ls=0.14, upper=True)
    tot = sum(langs.values()) or 1
    items = sorted(langs.items(), key=lambda kv: -kv[1])
    top = items[:6]
    rest = sum(v for _, v in items[6:])
    if rest:
        top.append(("Autres", rest))
    bx, bw, by = 32, 1136, 236
    s.add(f'<clipPath id="bar"><rect x="{bx}" y="{by}" width="{bw}" height="14" rx="7"/></clipPath>')
    s.add('<g clip-path="url(#bar)">')
    s.add(f'<rect x="{bx}" y="{by}" width="{bw}" height="14" fill="#fff" fill-opacity=".06"/>')
    cx = bx
    for i, (name, v) in enumerate(top):
        w = bw * v / tot
        s.add(f'<rect x="{cx:.1f}" y="{by}" width="{max(w - 2, 1):.1f}" height="14" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
        cx += w
    s.add(
        f'<rect x="{bx}" y="{by - 2}" width="{bw}" height="18" fill="{GROUND}">'
        f'<animate attributeName="x" values="{bx};{bx + bw}" dur="1.4s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .6 .2 1"/>'
        f'<animate attributeName="width" values="{bw};0" dur="1.4s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".2 .6 .2 1"/></rect>'
    )
    s.add("</g>")
    lx, ly = 32, 282
    for i, (name, v) in enumerate(top):
        s.add(f'<circle cx="{lx + 5}" cy="{ly - 5}" r="5" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
        s.text(lx + 18, ly, name, "Inter", 14, TEXT)
        nw = FONTOBJ["Inter"].width(name, 14)
        s.text(lx + 18 + nw + 10, ly, f"{100 * v / tot:.0f} %", "JetBrains Mono", 12, MUTED)
        lx += 18 + nw + 10 + 38 + 28
    s.save(out, "Statistiques GitHub", "Contributions, jours actifs, série, dépôts, étoiles et langages les plus utilisés.", common_defs(W, H))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    outdir = args[0] if args else "dist"
    os.makedirs(outdir, exist_ok=True)
    if "--sample" in sys.argv:
        days, n, stars, langs = sample()
    else:
        days = load_calendar()
        n, stars, langs = load_repos()
    contributions_svg(days, os.path.join(outdir, "contributions.svg"))
    stats_svg(days, n, stars, langs, os.path.join(outdir, "stats.svg"))
