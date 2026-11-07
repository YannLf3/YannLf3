#!/usr/bin/env python3
"""Génère les SVG statiques du README de profil (DA du portfolio). Texte converti en tracés : aucune police à charger.
Usage : python3 scripts/build_static_assets.py   (écrit dans assets/, nécessite fonttools et brotli)"""
import os, sys
from xml.sax.saxutils import escape
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from textpath import Font

FD = os.path.join(HERE, "fonts")
FONTOBJ = {
    "fraunces": Font(f"{FD}/fraunces-400.woff2"),
    "fraunces-i": Font(f"{FD}/fraunces-300-italic.woff2"),
    "inter": Font(f"{FD}/inter-400.woff2"),
    "mono": Font(f"{FD}/jetbrains-mono-400.woff2"),
}

GROUND, SURFACE, CARD = "#090b10", "#11141a", "#13161d"
TEXT, MUTED = "#f3f2ed", "#95989f"
ACCENT, ACCENT2 = "#00f8a8", "#00d3e5"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets")
os.makedirs(OUT, exist_ok=True)


def width(font, text, size, ls=0.0):
    return FONTOBJ[font].width(text, size, ls)


def wrap(font, text, size, maxw):
    lines, cur = [], ""
    for word in text.split(" "):
        test = (cur + " " + word).strip()
        if width(font, test, size) <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.body, self.defs = w, h, [], []

    def add(self, s):
        self.body.append(s)

    def text(self, x, y, s, font, size, fill, anchor="start", ls=0, opacity=1, extra="", upper=False, weight=None, children=""):
        if upper:
            s = s.upper()
        d = FONTOBJ[font].path(s, x, y, size, ls, anchor)
        bold = f' stroke="{fill}" stroke-width="{size * 0.035:.2f}" stroke-linejoin="round"' if weight and weight >= 600 else ""
        self.add(f'<g fill="{fill}" opacity="{opacity}"{bold} {extra}><path d="{d}"/>{children}</g>')

    def save(self, name, title, desc):
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
            f"<defs>{''.join(self.defs)}</defs>" + "".join(self.body) + "</svg>"
        )
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(name, f"{len(svg)/1024:.0f} Ko")


def typed(svg, uid, x, y, s, size, fill, start, step, cycle, font="mono"):
    """Texte qui s'écrit caractère par caractère (SMIL, rejoue en boucle). Retourne l'instant de fin."""
    cw = width(font, "M", size)
    n = len(s)
    times = [0.0] + [(start + i * step) / cycle for i in range(n)]
    vals = [0] + [round(width(font, s[: i + 1], size) + 1, 1) for i in range(n)]
    svg.defs.append(
        f'<clipPath id="{uid}"><rect x="{x}" y="{y - size - 4}" height="{size * 2}" width="0">'
        f'<animate attributeName="width" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{";".join(f"{t:.4f}" for t in times)}" values="{";".join(str(v) for v in vals)}"/></rect></clipPath>'
    )
    svg.text(x, y, s, font, size, fill, extra=f'clip-path="url(#{uid})"')
    return start + n * step


# ---------------------------------------------------------------- HERO
def hero():
    W, H = 1200, 470
    s = Svg(W, H)
    s.defs.append(
        f'<radialGradient id="glow" cx="82%" cy="12%" r="60%"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".16"/>'
        f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>'
        f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#fff" opacity=".07"/></pattern>'
        '<clipPath id="panel"><rect width="1200" height="470" rx="20"/></clipPath>'
    )
    s.add(f'<g clip-path="url(#panel)"><rect width="{W}" height="{H}" fill="{GROUND}"/>')
    s.add(f'<rect width="{W}" height="{H}" fill="url(#dots)"/><rect width="{W}" height="{H}" fill="url(#glow)"/>')
    # barre de titre
    s.add(f'<rect width="{W}" height="46" fill="{SURFACE}"/><line x1="0" y1="46" x2="{W}" y2="46" stroke="#fff" stroke-opacity=".09"/>')
    for cx, col in ((30, "#fb2c36"), (52, "#edb200"), (74, "#00c758")):
        s.add(f'<circle cx="{cx}" cy="23" r="6" fill="{col}" opacity=".8"/>')
    s.text(104, 28, "yann@portfolio:~ (zsh)", "mono", 13, MUTED)
    s.add("</g>")
    s.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="#fff" stroke-opacity=".18"/>')

    # pastille de disponibilité
    label = "Disponible pour missions · Available for work"
    ls = 0.08
    pw = width("mono", label.upper(), 12, ls) + 58
    s.add(f'<rect x="56" y="84" width="{pw:.0f}" height="34" rx="17" fill="#fff" fill-opacity=".04" stroke="#fff" stroke-opacity=".18"/>')
    s.add(f'<circle cx="77" cy="101" r="4" fill="{ACCENT}"><animate attributeName="opacity" values="1;.25;1" dur="2s" repeatCount="indefinite"/></circle>')
    s.text(92, 106, label, "mono", 12, MUTED, ls=ls, upper=True)

    # nom
    s.text(52, 222, "Yann", "fraunces", 108, TEXT, ls=-0.02)
    s.text(52, 328, "Le Flohic", "fraunces-i", 108, ACCENT, ls=-0.02)

    # accroche bilingue
    s.text(56, 378, "Sites vitrines, web apps et refontes sur mesure, du front à l'hébergement.", "inter", 18, TEXT, opacity=.85)
    s.text(56, 404, "Custom websites, web apps and redesigns, from front end to hosting.", "inter", 15, MUTED)
    s.text(56, 440, "Châteauroux · Limoges · FR", "mono", 11, MUTED, ls=0.14, upper=True)
    lx = 56 + width("mono", "Châteauroux · Limoges · FR".upper(), 11, 0.14) + 14
    s.add(f'<line x1="{lx:.0f}" y1="436" x2="{lx + 32:.0f}" y2="436" stroke="#fff" stroke-opacity=".25"/>')
    s.text(lx + 46, 440, "À distance · Remote", "mono", 11, MUTED, ls=0.14, upper=True)

    # terminal
    tx, ty, tw, th = 700, 88, 444, 330
    s.add(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="14" fill="{CARD}" stroke="#fff" stroke-opacity=".12"/>')
    s.add(f'<rect x="{tx}" y="{ty}" width="3" height="{th}" rx="1.5" fill="{ACCENT}" opacity=".9"/>')
    cycle, size, step = 17.0, 16, 0.075
    t = 0.8
    lines = [
        ("whoami", "yann, développeur full-stack", TEXT),
        ("cat services.txt", "site vitrine · web app · refonte", TEXT),
        ("ls ~/stack", "html css js php sql", TEXT),
        ("open yannleflohic.fr", "ouvert : yannleflohic.fr", ACCENT),
    ]
    y = ty + 48
    for i, (cmd, out, col) in enumerate(lines):
        s.text(tx + 24, y, "$", "mono", size, ACCENT, opacity=0,
               children=f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{(t - 0.1) / cycle:.4f}" values="0;1"/>')
        t = typed(s, f"c{i}", tx + 24 + width("mono", "$ ", size), y, cmd, size, TEXT, t, step, cycle)
        t += 0.25
        t = typed(s, f"o{i}", tx + 24, y + 28, out, size, col if col == ACCENT else MUTED, t, 0.035, cycle)
        t += 0.55
        y += 66
    s.text(tx + 24, y, "$", "mono", size, ACCENT, opacity=0,
           children=f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{t / cycle:.4f}" values="0;1"/>')
    blink_t = [0.0, t / cycle]
    k = 0
    while t + 0.5 * (k + 1) < cycle:
        blink_t.append((t + 0.5 * (k + 1)) / cycle); k += 1
    blink_v = ["0"] + ["1" if i % 2 == 0 else "0" for i in range(len(blink_t) - 1)]
    s.add(
        f'<rect x="{tx + 24 + width("mono", "$ ", size):.1f}" y="{y - 14}" width="9" height="19" fill="{ACCENT}" opacity="0">'
        f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{";".join(f"{x:.4f}" for x in blink_t)}" values="{";".join(blink_v)}"/></rect>'
    )
    s.save(
        "hero.svg",
        "Yann Le Flohic, développeur web full-stack freelance",
        "Bannière en forme de fenêtre de terminal : nom, disponibilité pour des missions, services et stack.",
    )


# ---------------------------------------------------------------- CARTES PROJETS
def card(fname, num, badge, pill, title, fr, en, tags, link, alt):
    W, H = 360, 372
    s = Svg(W, H)
    s.defs.append(
        f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".22"/>'
        f'<stop offset=".6" stop-color="{ACCENT2}" stop-opacity=".05"/><stop offset="1" stop-color="{GROUND}" stop-opacity="0"/></linearGradient>'
        '<pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#fff" opacity=".08"/></pattern>'
        f'<clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath>'
    )
    s.add(f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{CARD}"/>')
    s.add(f'<rect width="{W}" height="140" fill="{SURFACE}"/><rect width="{W}" height="140" fill="url(#dots)"/><rect width="{W}" height="140" fill="url(#g)"/></g>')
    s.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="#fff" stroke-opacity=".18"/>')
    s.text(24, 72, num, "fraunces-i", 50, TEXT)
    bw = width("mono", badge.upper(), 10, 0.12) + 24
    s.add(f'<rect x="{W - 24 - bw:.0f}" y="24" width="{bw:.0f}" height="26" rx="13" fill="{GROUND}" fill-opacity=".6" stroke="#fff" stroke-opacity=".22"/>')
    s.text(W - 24 - bw / 2, 41, badge, "mono", 10, TEXT, anchor="middle", ls=0.12, upper=True)
    pw = width("mono", pill.upper(), 10.5, 0.12) + 26
    s.add(f'<rect x="24" y="127" width="{pw:.0f}" height="26" rx="13" fill="{ACCENT}"/>')
    s.text(24 + pw / 2, 144, pill, "mono", 10.5, GROUND, anchor="middle", ls=0.12, upper=True, weight=700)
    s.text(24, 196, title, "fraunces", 24, TEXT, ls=-0.01)
    y = 224
    for ln in wrap("inter", fr, 13.5, W - 48):
        s.text(24, y, ln, "inter", 13.5, TEXT, opacity=.85); y += 19
    y += 4
    for ln in wrap("inter", en, 12.5, W - 48):
        s.text(24, y, ln, "inter", 12.5, MUTED); y += 17
    # tags
    x, ty = 24, 306
    for tg in tags:
        w = width("mono", tg.upper(), 9.5, 0.1) + 20
        s.add(f'<rect x="{x}" y="{ty}" width="{w:.0f}" height="24" rx="6" fill="{GROUND}" stroke="#fff" stroke-opacity=".16"/>')
        s.text(x + w / 2, ty + 16, tg, "mono", 9.5, ACCENT, anchor="middle", ls=0.1, upper=True)
        x += w + 8
    s.text(24, 352, link, "mono", 11, MUTED)
    s.save(fname, f"Projet {num} : {title}", alt)


def cards():
    card("card-01.svg", "01", "Client · Full-stack", "Professionnel", "Barcelona Feel Good Tours",
         "Site vitrine et back-office pour un guide touristique à Barcelone.",
         "Showcase site and admin panel for a tour guide in Barcelona.",
         ["PHP", "MySQL", "Tailwind"], "↗ barcelonafeelgoodtours.eu",
         "Carte du projet client Barcelona Feel Good Tours")
    card("card-02.svg", "02", "Perso · Full-stack", "Portfolio", "yannleflohic.fr",
         "Portfolio en PHP MVC avec back-office et deux modes, développeur et photographe.",
         "PHP MVC portfolio with an admin panel and two modes, developer and photographer.",
         ["PHP 8", "MySQL", "Tailwind"], "↗ yannleflohic.fr",
         "Carte du projet portfolio personnel")
    card("card-03.svg", "03", "Cours · Front + CMS", "WordPress", "Landing page WordPress",
         "Landing page fictive sur WordPress, réalisée en projet de cours (SAÉ 2.02).",
         "Fictional WordPress landing page built as a course project.",
         ["WordPress", "PHP", "CSS"], "↗ github.com/YannLf3/SAE202_Wordpress",
         "Carte du projet de cours WordPress")


# ---------------------------------------------------------------- STACK
def stack():
    W, H = 1200, 150
    s = Svg(W, H)
    s.defs.append('<clipPath id="c"><rect width="1200" height="150" rx="16"/></clipPath>')
    s.add(f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{GROUND}"/></g>')
    s.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="#fff" stroke-opacity=".14"/>')
    rows = [
        ("Front", ["HTML / CSS", "JavaScript", "Tailwind", "Sass", "BEM"]),
        ("Back & outils", ["PHP MVC", "SQL / MySQL", "Python", "WordPress", "Figma", "Hostinger"]),
    ]
    y = 22
    for label, items in rows:
        s.text(32, y + 24, label, "mono", 11, MUTED, ls=0.14, upper=True)
        x = 200
        for it in items:
            w = width("inter", it, 14) + 36
            s.add(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="36" rx="18" fill="{CARD}" stroke="#fff" stroke-opacity=".18"/>')
            s.text(x + w / 2, y + 23, it, "inter", 14, TEXT, anchor="middle")
            x += w + 12
        y += 58
    s.save("stack.svg", "Stack technique", "Front : HTML, CSS, JavaScript, Tailwind, Sass, BEM. Back et outils : PHP MVC, SQL, Python, WordPress, Figma, Hostinger.")


ARROW_R = "M0 0h14M9 -5l5 5-5 5"            # flèche vers la droite
ARROW_NE = "M0 7L12 -5M4 -5h8v8"             # flèche externe
ENTER = "M12 -6v6H1M5 -4L1 0l4 4"            # touche entrée
CHEV = "M0 0l5 5 5-5"                        # chevron vers le bas


def defs_common(s, W, H, rx=16, glow=True):
    s.defs.append(
        f'<radialGradient id="glow" cx="90%" cy="0%" r="70%"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".14"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>'
        '<pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="#fff" opacity=".07"/></pattern>'
        f'<clipPath id="panel"><rect width="{W}" height="{H}" rx="{rx}"/></clipPath>'
    )


def button(fname, label, primary=False, external=False, alt=""):
    size = 15
    tw = width("inter", label, size)
    W, H = int(tw + 34 + 30), 46
    s = Svg(W, H)
    fill, stroke, tcol = (ACCENT, "none", GROUND) if primary else (CARD, "#fff", TEXT)
    s.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="23" fill="{fill}" stroke="{stroke}" stroke-opacity=".22"/>')
    s.text(22, 29, label, "inter", size, tcol, weight=600 if primary else None)
    ax = W - 36
    s.add(f'<path transform="translate({ax} 23)" d="{ARROW_NE if external else ARROW_R}" fill="none" stroke="{tcol}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
    s.save(fname, label, alt or label)


def buttons():
    button("btn-contact.svg", "Me contacter", primary=True, alt="Me contacter par email")
    button("btn-malt.svg", "Malt", external=True)
    button("btn-linkedin.svg", "LinkedIn", external=True)
    button("btn-instagram.svg", "Instagram", external=True)
    button("btn-portfolio.svg", "Portfolio", external=True)


def cmd_row(fname, cmd, desc, external=False, header=False):
    W, H = 1200, 56
    s = Svg(W, H)
    s.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14" fill="{SURFACE if header else CARD}" stroke="#fff" stroke-opacity="{.09 if header else .14}"/>')
    if header:
        s.add(f'<circle cx="30" cy="28" r="6" fill="#fb2c36" opacity=".8"/><circle cx="52" cy="28" r="6" fill="#edb200" opacity=".8"/><circle cx="74" cy="28" r="6" fill="#00c758" opacity=".8"/>')
        s.text(104, 33, "Aller à · Jump to", "mono", 14, MUTED)
        kx = W - 40 - 118
        for lab, w in (("Ctrl", 56), ("K", 36)):
            s.add(f'<rect x="{kx}" y="15" width="{w}" height="26" rx="6" fill="{GROUND}" stroke="#fff" stroke-opacity=".22"/>')
            s.text(kx + w / 2, 33, lab, "mono", 12, TEXT, anchor="middle")
            kx += w + 8
        s.save(fname, "Navigation rapide", "Barre de navigation rapide façon terminal")
        return
    s.add(f'<rect x="0" y="14" width="3" height="28" rx="1.5" fill="{ACCENT}"/>')
    s.text(32, 34, "$", "mono", 17, ACCENT)
    s.text(56, 34, cmd, "mono", 17, TEXT)
    s.text(430, 33, desc, "inter", 15, MUTED)
    s.add(f'<rect x="{W-72}" y="14" width="40" height="28" rx="7" fill="{GROUND}" stroke="#fff" stroke-opacity=".22"/>')
    s.add(f'<path transform="translate({W-58} 28)" d="{ARROW_NE if external else ENTER}" fill="none" stroke="{TEXT}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    s.save(fname, cmd, desc)


def cmds():
    cmd_row("cmd-header.svg", "", "", header=True)
    cmd_row("cmd-projets.svg", "open projets", "Voir mes réalisations")
    cmd_row("cmd-services.svg", "open services", "Ce que je peux faire pour vous")
    cmd_row("cmd-contributions.svg", "open contributions", "Mon activité et mes stats GitHub")
    cmd_row("cmd-contact.svg", "open contact", "Parler de votre projet")
    cmd_row("cmd-portfolio.svg", "open portfolio", "yannleflohic.fr", external=True)


def lang_toggle(fname, label, key):
    size = 15
    W, H = int(width("inter", label, size) + 118), 46
    s = Svg(W, H)
    s.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="23" fill="{CARD}" stroke="#fff" stroke-opacity=".22"/>')
    s.add(f'<rect x="14" y="11" width="34" height="24" rx="6" fill="{ACCENT}"/>')
    s.text(31, 28, key, "mono", 12, GROUND, anchor="middle", weight=700)
    s.text(60, 29, label, "inter", size, TEXT)
    s.add(f'<g transform="translate({W-34} 20)"><path d="{CHEV}" fill="none" stroke="{TEXT}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
          '<animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;0 3;0 0" dur="1.8s" repeatCount="indefinite"/></g>')
    s.save(fname, label, label)


def project(fname, num, badge, title, desc, tags, alt):
    W, H = 1200, 188
    s = Svg(W, H)
    defs_common(s, W, H, rx=20)
    s.defs.append(f'<linearGradient id="lg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".16"/><stop offset=".45" stop-color="{ACCENT2}" stop-opacity=".04"/><stop offset="1" stop-color="{GROUND}" stop-opacity="0"/></linearGradient>')
    s.add(f'<g clip-path="url(#panel)"><rect width="{W}" height="{H}" fill="{CARD}"/><rect width="{W}" height="{H}" fill="url(#dots)"/><rect width="{W}" height="{H}" fill="url(#lg)"/><rect width="4" height="{H}" fill="{ACCENT}"/></g>')
    s.add(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="#fff" stroke-opacity=".18"/>')
    s.text(40, 112, num, "fraunces-i", 76, TEXT)
    tx = 170
    s.text(tx, 70, title, "fraunces", 32, TEXT, ls=-0.01)
    y = 104
    for ln in wrap("inter", desc, 16, 640):
        s.text(tx, y, ln, "inter", 16, TEXT, opacity=.82); y += 24
    x = tx
    for tg in tags:
        w = width("mono", tg.upper(), 10, 0.1) + 22
        s.add(f'<rect x="{x}" y="142" width="{w:.0f}" height="26" rx="7" fill="{GROUND}" stroke="#fff" stroke-opacity=".16"/>')
        s.text(x + w / 2, 159, tg, "mono", 10, ACCENT, anchor="middle", ls=0.1, upper=True)
        x += w + 8
    bw = width("mono", badge.upper(), 10.5, 0.12) + 26
    s.add(f'<rect x="{W - 40 - bw:.0f}" y="28" width="{bw:.0f}" height="28" rx="14" fill="{GROUND}" fill-opacity=".6" stroke="#fff" stroke-opacity=".22"/>')
    s.text(W - 40 - bw / 2, 46, badge, "mono", 10.5, TEXT, anchor="middle", ls=0.12, upper=True)
    # bouton « détail » avec chevron animé
    lab = "Voir le détail"
    pw = width("inter", lab, 14) + 62
    px = W - 40 - pw
    s.add(f'<rect x="{px:.0f}" y="124" width="{pw:.0f}" height="44" rx="22" fill="none" stroke="{ACCENT}" stroke-opacity=".7"/>')
    s.text(px + 22, 151, lab, "inter", 14, ACCENT)
    s.add(f'<g transform="translate({px + pw - 34:.0f} 143)"><path d="{CHEV}" fill="none" stroke="{ACCENT}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
          '<animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;0 3;0 0" dur="1.8s" repeatCount="indefinite"/></g>')
    s.save(fname, f"Projet {num} : {title}", alt)


def projects():
    project("project-01.svg", "01", "Client · Full-stack", "Barcelona Feel Good Tours",
            "Site vitrine et back-office pour une guide touristique à Barcelone. Le contenu se gère en autonomie depuis l'administration.",
            ["PHP", "MySQL", "Tailwind", "Hostinger"], "Projet client Barcelona Feel Good Tours")
    project("project-02.svg", "02", "Perso · Full-stack", "yannleflohic.fr",
            "Mon portfolio en PHP MVC, avec back-office, thème clair et sombre, et deux modes selon que l'on vient pour le code ou pour la photo.",
            ["PHP 8", "MySQL", "Tailwind", "JavaScript"], "Projet portfolio personnel")
    project("project-03.svg", "03", "Cours · Front + CMS", "Landing page WordPress",
            "Landing page fictive réalisée sur WordPress dans le cadre d'une SAÉ du BUT MMI.",
            ["WordPress", "PHP", "CSS"], "Projet de cours WordPress")


if __name__ == "__main__":
    hero(); stack(); buttons(); cmds(); projects()
    lang_toggle("lang-en.svg", "Read in English", "EN")
