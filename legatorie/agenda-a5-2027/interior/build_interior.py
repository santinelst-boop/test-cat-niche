"""Interior agendă A5 2027 – Școala Gimnazială „1 Decembrie 1918” Alba Iulia.

Pornește de la interiorul Golden Silo (dublaj A4, 172 pagini) și:
  1. extrage pagina A5 din fiecare coală A4 (pe A4 e aceeași pagină de 2 ori);
  2. trece tot conținutul în MONOCROM (tonuri de negru), cu liniile prea
     deschise întărite la minimum 20% negru, ca să nu se piardă la tipar;
  3. scoate datele Golden Silo (pag. 1 prezentare, sigla și câmpurile
     FUNCȚIA/COMPANIA de la pag. 3, antetul „GOLDEN SILO” de pe pag. 5–172)
     și pune datele școlii, cu fonturile originale (Cinzel, Cormorant Garamond);
  4. mărește marginea de la cotor cu GUTTER_EXTRA mm păstrând pagina CENTRATĂ:
     conținutul se micșorează uniform față de centrul paginii, astfel încât
     cea mai mică margine laterală din original (12 mm) devine 15 mm;
  5. refacere dublaj A4 identic cu originalul (A5 la x=0,709 pt și x=421,654 pt).
Ieșiri: interior A5 (172 pag.) și dublaj A4 (172 pag.).
"""
import io
import math
from pathlib import Path

import pikepdf
import pymupdf
from pikepdf import Array, Dictionary, Name, Operator
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).parent
SRC = HERE / "sursa" / "GoldenSilo_interior_agenda_A5_2027_DUBLAJ_A4.pdf"
COVER = HERE.parent / "sursa" / "coperta_agenda_a5_grafica.pdf"
OUT_A5 = HERE / "Agenda_A5_2027_interior_172pag_MONOCROM.pdf"
OUT_A4 = HERE / "Agenda_A5_2027_interior_172pag_MONOCROM_DUBLAJ_A4.pdf"

A5_W, A5_H = 419.52757, 595.2756
A4_W, A4_H = 841.89, 595.276
DUBLAJ_X = (0.70866, 421.6535)          # pozițiile A5 pe A4, ca în original
GUTTER_EXTRA = 3                        # mm în plus la cotor (și la exterior)
MIN_SIDE_MARGIN = 12                    # mm, cea mai mică margine laterală din original
MIN_STROKE_BLACK = 0.20                 # liniile: minimum 20% negru

SCHOOL = "ȘCOALA GIMNAZIALĂ „1 DECEMBRIE 1918”"
ADDRESS = "Calea Moților 224, Alba Iulia, Alba, România"
CONTACT = "Tel: 0744.393.297  ·  0763.634.148  ·  sp1dec1918@gmail.com"
FIELDS = {"FUNCȚIA": "CLASA", "COMPANIA": "ȘCOALA"}   # pag. 3, date personale
REMOVE = ("GOLDEN SILO", "FUNCȚIA", "COMPANIA")

pdfmetrics.registerFont(TTFont("Cinzel", str(HERE / "fonts" / "Cinzel-SemiBold.ttf")))
pdfmetrics.registerFont(TTFont("Cormorant", str(HERE / "fonts" / "CormorantGaramond-Medium.ttf")))


# ---------------------------------------------------------------- culoare
def cmyk_gray(c, m, y, k):
    return max(0.0, 1 - min(1.0, 0.30 * c + 0.59 * m + 0.11 * y + k))


def rgb_gray(r, g, b):
    return 0.30 * r + 0.59 * g + 0.11 * b


def to_gray(vals):
    vals = [float(v) for v in vals]
    if len(vals) == 4:
        return cmyk_gray(*vals)
    if len(vals) == 3:
        return rgb_gray(*vals)
    return vals[0]


def ncomp(cs, resources):
    """Numărul de componente al unui spațiu de culoare numit."""
    name = str(cs)
    std = {"/DeviceGray": 1, "/DeviceRGB": 3, "/DeviceCMYK": 4, "/CalGray": 1, "/CalRGB": 3}
    if name in std:
        return std[name]
    obj = resources.get("/ColorSpace", {}).get(name) if resources is not None else None
    if isinstance(obj, pikepdf.Array):
        kind = str(obj[0])
        if kind == "/ICCBased":
            return int(obj[1].get("/N", 3))
        if kind == "/Pattern":
            return 0
        return std.get(kind, 4)
    return 4


def mul(a, b):
    """Produs de matrice PDF [a b c d e f]."""
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3],
            a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def apply(m, x, y):
    return m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]


# ---------------------------------------------------------------- rescriere fluxuri
class Rewriter:
    """Trece fluxurile în gri, scoate imagini și textele din zonele date."""

    def __init__(self, drop_images=False):
        self.done = set()
        self.drop_images = drop_images
        self.removed = []           # (x, y, size, gray) pentru fiecare text scos

    def form(self, xo, ctm, rects):
        if xo.objgen in self.done:
            return
        self.done.add(xo.objgen)
        res = xo.get("/Resources")
        out = []
        stack = []
        cs_fill = cs_stroke = 4
        fill_gray = 0.0
        tm = tlm = [1, 0, 0, 1, 0, 0]
        tl = 0.0
        size = 0.0

        def text_hit():
            x, y = apply(mul(tm, ctm), 0, 0)
            for (x0, y0, x1, y1, s) in rects:
                if x0 <= x <= x1 and y0 <= y <= y1 and abs(size - s) < 0.6:
                    self.removed.append((x, y, size, fill_gray))
                    return True
            return False

        for operands, op in pikepdf.parse_content_stream(xo):
            o = str(op)
            if o == "q":
                stack.append(ctm)
            elif o == "Q":
                ctm = stack.pop() if stack else ctm
            elif o == "cm":
                ctm = mul([float(v) for v in operands], ctm)
            elif o in ("k", "rg"):
                fill_gray = to_gray(operands)
                out.append(([fill_gray], Operator("g")))
                continue
            elif o in ("K", "RG"):
                out.append(([min(to_gray(operands), 1 - MIN_STROKE_BLACK)], Operator("G")))
                continue
            elif o == "g":
                fill_gray = float(operands[0])
            elif o == "G":
                out.append(([min(float(operands[0]), 1 - MIN_STROKE_BLACK)], Operator("G")))
                continue
            elif o in ("cs", "CS"):
                n = ncomp(operands[0], res)
                if n:
                    if o == "cs":
                        cs_fill = n
                    else:
                        cs_stroke = n
                    out.append(([Name("/DeviceGray")], op))
                    continue
            elif o in ("sc", "scn", "SC", "SCN"):
                nums = [v for v in operands if not isinstance(v, pikepdf.Name)]
                if len(nums) == len(operands) and nums:
                    g = to_gray(nums)
                    if o in ("sc", "scn"):
                        fill_gray = g
                    else:
                        g = min(g, 1 - MIN_STROKE_BLACK)
                    out.append(([g], op))
                    continue
            elif o == "BT":
                tm = tlm = [1, 0, 0, 1, 0, 0]
            elif o == "Tf":
                size = float(operands[1])
            elif o == "TL":
                tl = float(operands[0])
            elif o == "Tm":
                tm = tlm = [float(v) for v in operands]
            elif o in ("Td", "TD"):
                tx, ty = float(operands[0]), float(operands[1])
                if o == "TD":
                    tl = -ty
                tm = tlm = mul([1, 0, 0, 1, tx, ty], tlm)
            elif o == "T*":
                tm = tlm = mul([1, 0, 0, 1, 0, -tl], tlm)
            elif o in ("'", '"'):
                tm = tlm = mul([1, 0, 0, 1, 0, -tl], tlm)
                if text_hit():
                    continue
            elif o in ("Tj", "TJ"):
                if text_hit():
                    continue
            elif o == "Do" and res is not None:
                xobj = res.get("/XObject", {}).get(str(operands[0]))
                if xobj is not None:
                    if xobj.get("/Subtype") == "/Image" and self.drop_images:
                        continue
                    if xobj.get("/Subtype") == "/Form":
                        m = [float(v) for v in xobj.get("/Matrix", [1, 0, 0, 1, 0, 0])]
                        self.form(xobj, mul(m, ctm), rects)
            out.append((operands, op))
        xo.write(pikepdf.unparse_content_stream(out))


# ---------------------------------------------------------------- texte de înlocuit
def find_spans(src_path):
    """Pentru fiecare pagină A5: zonele de scos și pozițiile textelor (coord. PDF)."""
    doc = pymupdf.open(src_path)
    pages = []
    for p in doc:
        found = []
        for b in p.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for s in line["spans"]:
                    t = s["text"].replace("\xa0", " ").strip()
                    x0, y0, x1, y1 = s["bbox"]
                    if t in REMOVE and x0 < DUBLAJ_X[1]:
                        found.append(dict(text=t, size=s["size"],
                                          x0=x0 - DUBLAJ_X[0], x1=x1 - DUBLAJ_X[0],
                                          y0=A5_H - y1, y1=A5_H - y0,
                                          base=A5_H - s["origin"][1]))
        pages.append(found)
    return pages


def tracking(text, size, width):
    """Spațierea dintre litere folosită în original."""
    natural = pdfmetrics.stringWidth(text, "Cinzel", size)
    return (width - natural) / max(1, len(text) - 1)


# ---------------------------------------------------------------- sigla școlii (vectorial)
def circle_ops(cx, cy, r):
    c = 0.5523 * r
    return (f"{cx + r:.3f} {cy:.3f} m "
            f"{cx + r:.3f} {cy + c:.3f} {cx + c:.3f} {cy + r:.3f} {cx:.3f} {cy + r:.3f} c "
            f"{cx - c:.3f} {cy + r:.3f} {cx - r:.3f} {cy + c:.3f} {cx - r:.3f} {cy:.3f} c "
            f"{cx - r:.3f} {cy - c:.3f} {cx - c:.3f} {cy - r:.3f} {cx:.3f} {cy - r:.3f} c "
            f"{cx + c:.3f} {cy - r:.3f} {cx + r:.3f} {cy - c:.3f} {cx + r:.3f} {cy:.3f} c h")


LOGO_C, LOGO_R = (209.5277, 297.4357), 137.6     # cercul siglei pe copertă


def logo_ops(name, cx, cy, diameter):
    s = diameter / (2 * LOGO_R)
    tx, ty = cx - s * LOGO_C[0], cy - s * LOGO_C[1]
    return (f"q {circle_ops(cx, cy, diameter / 2)} W n "
            f"{s:.5f} 0 0 {s:.5f} {tx:.3f} {ty:.3f} cm /{name} Do Q")


# ---------------------------------------------------------------- strat nou (texte școală)
def overlay(spans, n_pages):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(A5_W, A5_H), initialFontName="Cinzel")
    for i in range(n_pages):
        c.setFillGray(0)
        if i == 0:
            cover_page(c)
        for s in spans[i]:
            if s["text"] == "GOLDEN SILO":
                ts = tracking("GOLDEN SILO", s["size"], s["x1"] - s["x0"])
                c.setFillGray(s.get("gray", 0.35))
                t = c.beginText()
                t.setFont("Cinzel", s["size"])
                t.setCharSpace(ts)
                w = pdfmetrics.stringWidth(SCHOOL, "Cinzel", s["size"]) + ts * (len(SCHOOL) - 1)
                t.setTextOrigin(s["x1"] - w, s["base"])
                t.textOut(SCHOOL)
                c.drawText(t)
            elif s["text"] in FIELDS:
                c.setFillGray(s.get("gray", 0))
                t = c.beginText()
                t.setFont("Cinzel", s["size"])
                t.setCharSpace(tracking(s["text"], s["size"], s["x1"] - s["x0"]))
                t.setTextOrigin(s["x0"], s["base"])
                t.textOut(FIELDS[s["text"]])
                c.drawText(t)
        c.showPage()
    c.save()
    return pikepdf.open(io.BytesIO(buf.getvalue()))


def centered(c, text, font, size, y, space=0.0, gray=0.0):
    c.setFillGray(gray)
    w = pdfmetrics.stringWidth(text, font, size) + space * (len(text) - 1)
    t = c.beginText()
    t.setFont(font, size)
    t.setCharSpace(space)
    t.setTextOrigin(A5_W / 2 - w / 2, y)
    t.textOut(text)
    c.drawText(t)


def cover_page(c):
    """Pagina 1: prezentarea școlii, în locul celei Golden Silo (aceeași așezare)."""
    centered(c, "ȘCOALA GIMNAZIALĂ", "Cinzel", 11.98, A5_H - 300.5, 0.6)
    centered(c, "„1 DECEMBRIE 1918”", "Cinzel", 11.98, A5_H - 318.3, 0.6)
    c.setStrokeGray(0.35)
    c.setLineWidth(0.6)
    c.line(A5_W / 2 - 28, A5_H - 332, A5_W / 2 + 28, A5_H - 332)
    centered(c, "Alba Iulia", "Cormorant", 9.87, A5_H - 351.5)
    centered(c, "AGENDA  2027", "Cinzel", 7.4, A5_H - 392.5, 1.2, gray=0.35)
    centered(c, SCHOOL, "Cinzel", 7.75, A5_H - 515.6, 0.9)
    centered(c, ADDRESS, "Cormorant", 8.1, A5_H - 528.2)
    centered(c, CONTACT, "Cormorant", 8.1, A5_H - 539.8)


# ---------------------------------------------------------------- asamblare
def build():
    src = pikepdf.open(SRC)
    spans = find_spans(SRC)
    n = len(src.pages)

    # zonele de scos, pe pagină (coordonate A5)
    rw = Rewriter(drop_images=True)
    out = pikepdf.new()

    # sigla școlii din copertă, trecută și ea în gri
    cover = pikepdf.open(COVER)
    logo = out.copy_foreign(cover.pages[0].as_form_xobject())
    Rewriter().form(logo, [1, 0, 0, 1, 0, 0], [])

    page_forms = []
    for i, sp in enumerate(src.pages):
        outer = sp.Resources.XObject.Fm0            # copia din stânga
        rects = [(s["x0"] - 1, s["y0"] - 1, s["x1"] + 1, s["y1"] + 1, s["size"]) for s in spans[i]]
        removed_before = len(rw.removed)
        for inner in outer.Resources.XObject.values():
            m = [float(v) for v in inner.get("/Matrix", [1, 0, 0, 1, 0, 0])]
            rw.form(inner, m, rects)
        # culoarea (gri) a textului scos, ca textul nou să aibă aceeași nuanță
        grays = [g for (_, _, _, g) in rw.removed[removed_before:]]
        for s in spans[i]:
            if grays:
                s["gray"] = grays[0]
        page_forms.append(outer)

    ov = overlay(spans, n)
    # micșorare uniformă față de centru: marginea de 12 mm devine 15 mm
    sc = 1 - GUTTER_EXTRA * mm / (A5_W / 2 - MIN_SIDE_MARGIN * mm)
    tx, ty = (1 - sc) * A5_W / 2, (1 - sc) * A5_H / 2
    for i in range(n):
        page = out.add_blank_page(page_size=(A5_W, A5_H))
        xobj = Dictionary()
        ops = [f"q {sc:.5f} 0 0 {sc:.5f} {tx:.4f} {ty:.4f} cm"]
        if i != 0:                                    # pag. 1 se refa complet
            pf = out.copy_foreign(page_forms[i])
            pf.Matrix = Array([1, 0, 0, 1, 0, 0])
            xobj["/Pg"] = pf
            ops.append("/Pg Do")
        xobj["/Ov"] = out.copy_foreign(ov.pages[i].as_form_xobject())
        ops.append("/Ov Do")
        if i == 0:
            xobj["/Logo"] = logo
            ops.append(logo_ops("Logo", A5_W / 2, A5_H - 150.4, 150))
        if i == 2:
            xobj["/Logo"] = logo
            ops.append(logo_ops("Logo", A5_W / 2, A5_H - 72.5, 52))
        ops.append("Q")
        page.Resources = Dictionary(XObject=xobj)
        page.Contents = out.make_stream(" ".join(ops).encode())
    out.docinfo["/Title"] = "Agenda A5 2027 – interior monocrom – Școala Gimnazială „1 Decembrie 1918”"
    out.save(OUT_A5)
    print("text scos:", len(rw.removed), "| pagini cu înlocuiri:", sum(1 for s in spans if s))

    # dublaj A4: aceeași pagină A5 de două ori, ca în original
    a5 = pikepdf.open(OUT_A5)
    dub = pikepdf.new()
    for i in range(n):
        f = dub.copy_foreign(a5.pages[i].as_form_xobject())
        page = dub.add_blank_page(page_size=(A4_W, A4_H))
        page.Resources = Dictionary(XObject=Dictionary(A=f))
        page.Contents = dub.make_stream(
            " ".join(f"q 1 0 0 1 {x} 0 cm /A Do Q" for x in DUBLAJ_X).encode())
    dub.docinfo["/Title"] = "Agenda A5 2027 – interior monocrom – dublaj A4"
    dub.save(OUT_A4)
    print("ok", OUT_A5.name, OUT_A4.name)


if __name__ == "__main__":
    build()
