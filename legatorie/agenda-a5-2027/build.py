"""Copertă agendă A5 2027 – Școala Gimnazială „1 Decembrie 1918” Alba Iulia.

Montaj identic cu „GoldenSilo_coperta_agenda_A5_2027_SRA3.pdf”:
  coală SRA3 orizontală 450 x 320 mm, STÂNGA = FAȚĂ, DREAPTA = SPATE
  carton 148 x 210 mm, întoarcere 20 mm, bleed 3 mm
  -> format tăiat 188 x 250 mm, cu bleed 194 x 256 mm
  semne de tăiere 5 mm, 0,25 pt, registration (1 1 1 1 K)
  semne albe 0,5 pt pe întoarcere: muchia cartonului + mijloc
Grafica originală (vectorială, CMYK cu profilul ICC din CorelDRAW) stă exact pe
carton; fondul galben și liniile verzi se prelungesc pe întoarcere și bleed.
"""
import io
from pathlib import Path

import pikepdf
from pikepdf import Array, Dictionary
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

SHEET_W, SHEET_H = 450, 320
BOARD_W, BOARD_H = 148, 210
WRAP, BLEED = 20, 3
CUT_W, CUT_H = BOARD_W + 2 * WRAP, BOARD_H + 2 * WRAP      # 188 x 250
PIECE_X = [24, 238]                                          # x tăiere: față, spate
CUT_Y = (SHEET_H - CUT_H) / 2                                # 35
MARK_LEN = 5

YELLOW = "0 0.2510 0.8510 0.1020"
GREEN = "0.9490 0.1882 0.7020 0.7216"
# liniile verzi din grafica originală (y jos/sus în pt, față de colțul cartonului)
LINES = [[(71.7780, 74.6127)], [(71.7780, 74.6127), (507.7860, 510.6206)]]

SLUG = ("Agenda A5 2027 · Școala Gimnazială „1 Decembrie 1918” Alba Iulia · "
        f"carton {BOARD_W}×{BOARD_H} mm · întoarcere {WRAP} mm · bleed {BLEED} mm"
        " — STÂNGA: FAȚĂ   DREAPTA: SPATE")
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

HERE = Path(__file__).parent
SRC = HERE / "sursa" / "coperta_agenda_a5_grafica.pdf"
OUT = HERE / "Agenda_A5_2027_coperta_SRA3_cu_semne.pdf"


def overlay():
    """Semne de tăiere, semne albe de carton și textul de identificare."""
    buf = io.BytesIO()
    pdfmetrics.registerFont(TTFont("LiberationSans", FONT))
    c = canvas.Canvas(buf, pagesize=(SHEET_W * mm, SHEET_H * mm),
                      initialFontName="LiberationSans")
    y0, y1 = CUT_Y, CUT_Y + CUT_H
    for x in PIECE_X:
        x1 = x + CUT_W
        # semne de tăiere, pornesc de la marginea bleed-ului
        c.setLineWidth(0.25)
        c.setStrokeColorCMYK(1, 1, 1, 1)
        for xx in (x, x1):
            c.line(xx * mm, (y0 - BLEED - MARK_LEN) * mm, xx * mm, (y0 - BLEED) * mm)
            c.line(xx * mm, (y1 + BLEED) * mm, xx * mm, (y1 + BLEED + MARK_LEN) * mm)
        for yy in (y0, y1):
            c.line((x - BLEED - MARK_LEN) * mm, yy * mm, (x - BLEED) * mm, yy * mm)
            c.line((x1 + BLEED) * mm, yy * mm, (x1 + BLEED + MARK_LEN) * mm, yy * mm)
        # semne albe pe întoarcere: muchia cartonului și mijlocul
        c.setLineWidth(0.5)
        c.setStrokeColorCMYK(0, 0, 0, 0)
        bx0, bx1, by0, by1 = x + WRAP, x1 - WRAP, y0 + WRAP, y1 - WRAP
        mid = x + CUT_W / 2
        for xx in (bx0, bx1, mid):
            c.line(xx * mm, (y0 + 4.5) * mm, xx * mm, (y0 + 7.5) * mm)
            c.line(xx * mm, (y1 - 7.5) * mm, xx * mm, (y1 - 4.5) * mm)
        c.line((mid - 1.5) * mm, (y1 - 6) * mm, (mid + 1.5) * mm, (y1 - 6) * mm)
        for yy in (by0, by1):
            c.line(x * mm, yy * mm, (x + 3) * mm, yy * mm)
            c.line((x1 - 3) * mm, yy * mm, x1 * mm, yy * mm)
    c.setFont("LiberationSans", 8)
    c.setFillColorCMYK(0, 0, 0, 1)
    c.drawString(21 * mm, 8 * mm, SLUG)
    c.save()
    return pikepdf.open(io.BytesIO(buf.getvalue()))


def build():
    src = pikepdf.open(SRC)
    out = pikepdf.new()
    W, H = SHEET_W * mm, SHEET_H * mm
    page = out.add_blank_page(page_size=(W, H))
    res = src.pages[0].Resources
    xobj = Dictionary()
    ops = ["/GS0 gs /CS0 cs /CS0 CS"]
    for i, sp in enumerate(src.pages):
        xobj[f"/Fx{i}"] = out.copy_foreign(sp.as_form_xobject())
        x = PIECE_X[i]
        bx, by = (x - BLEED) * mm, (CUT_Y - BLEED) * mm
        bw, bh = (CUT_W + 2 * BLEED) * mm, (CUT_H + 2 * BLEED) * mm
        ax, ay = (x + WRAP) * mm, (CUT_Y + WRAP) * mm
        ops.append(f"q {bx:.4f} {by:.4f} {bw:.4f} {bh:.4f} re W n")
        ops.append(f"{YELLOW} scn {bx:.4f} {by:.4f} {bw:.4f} {bh:.4f} re f")
        for y0, y1 in LINES[i]:
            ops.append(f"{GREEN} scn {GREEN} SCN 0.5 w {bx:.4f} {ay + y0:.4f} {bw:.4f} {y1 - y0:.4f} re b")
        ops.append(f"q 1 0 0 1 {ax:.4f} {ay:.4f} cm /Fx{i} Do Q Q")
    ov = overlay()
    xobj["/Ov"] = out.copy_foreign(ov.pages[0].as_form_xobject())
    ops.append("q /Ov Do Q")
    page.Resources = Dictionary(
        XObject=xobj,
        ColorSpace=Dictionary(CS0=out.copy_foreign(res.ColorSpace.CS14)),
        ExtGState=Dictionary(GS0=out.copy_foreign(res.ExtGState.GS13)),
    )
    page.Contents = out.make_stream("\n".join(ops).encode())
    out.docinfo["/Title"] = "Agenda A5 2027 – copertă SRA3 cu semne"
    out.save(OUT)


if __name__ == "__main__":
    build()
    print("ok", OUT.name)
