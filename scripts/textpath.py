"""Convertit du texte en tracés SVG (aucune police à charger côté navigateur). Nécessite fonttools et brotli."""
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen


def _n(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


class Font:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.cmap = self.tt.getBestCmap()
        self.gs = self.tt.getGlyphSet()
        self.hmtx = self.tt["hmtx"]
        self.upm = self.tt["head"].unitsPerEm

    def _g(self, ch):
        return self.cmap.get(ord(ch)) or self.cmap.get(ord("?"))

    def width(self, text, size, ls=0.0):
        s = size / self.upm
        return sum(self.hmtx[self._g(c)][0] * s + ls * size for c in text)

    def path(self, text, x, y, size, ls=0.0, anchor="start"):
        w = self.width(text, size, ls)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        pen = SVGPathPen(self.gs, ntos=_n)
        s, cx = size / self.upm, x
        for ch in text:
            g = self._g(ch)
            self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
            cx += self.hmtx[g][0] * s + ls * size
        return pen.getCommands()
