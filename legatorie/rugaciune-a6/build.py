"""Montaj „Ai nevoie de rugăciune?” A6 4-up pe SRA4, față-verso.

Același montaj ca „Momentum A6 4-up SRA4”:
  coală SRA4 225 x 320 mm, 2 x 2 bucăți A6 105 x 148 mm,
  bleed 3 mm, tăiere comună (cotor 0), semne de tăiere 0,25 pt registration.
Pagina 1 = față, pagina 2 = verso (întoarcere pe latura lungă; montajul e
simetric, deci verso-ul cade exact pe față).
Imaginile sursă nu au bleed: se scalează pe lățimea A6, se taie la 148 mm
înălțime și se prelungesc 3 mm prin repetarea pixelilor de margine.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

SHEET_W, SHEET_H = 225, 320
TRIM_W, TRIM_H = 105, 148
BLEED = 3
COLS, ROWS = 2, 2
X0 = (SHEET_W - COLS * TRIM_W) / 2   # 7.5 mm
Y0 = (SHEET_H - ROWS * TRIM_H) / 2   # 12 mm
NAME = "Ai nevoie de rugaciune"

HERE = Path(__file__).parent
PAGES = [HERE / "sursa" / "fata.jpg", HERE / "sursa" / "verso.jpg"]


def with_bleed(path):
    im = Image.open(path).convert("RGB")
    px_mm = im.width / TRIM_W
    h = round(TRIM_H * px_mm)
    top = (im.height - h) // 2
    a = np.asarray(im)[top:top + h]
    b = round(BLEED * px_mm)
    return Image.fromarray(np.pad(a, ((b, b), (b, b), (0, 0)), mode="edge"))


def build(out):
    c = canvas.Canvas(str(out), pagesize=(SHEET_W * mm, SHEET_H * mm))
    c.setTitle(f"{NAME} – A6 4-up pe SRA4")
    for path in PAGES:
        img = ImageReader(with_bleed(path))
        for r in range(ROWS):
            for col in range(COLS):
                tx, ty = X0 + col * TRIM_W, Y0 + r * TRIM_H
                # zona vizibilă a fiecărei bucăți: bleed doar spre marginea colii
                cx0 = tx - (BLEED if col == 0 else 0)
                cx1 = tx + TRIM_W + (BLEED if col == COLS - 1 else 0)
                cy0 = ty - (BLEED if r == 0 else 0)
                cy1 = ty + TRIM_H + (BLEED if r == ROWS - 1 else 0)
                c.saveState()
                p = c.beginPath()
                p.rect(cx0 * mm, cy0 * mm, (cx1 - cx0) * mm, (cy1 - cy0) * mm)
                c.clipPath(p, stroke=0, fill=0)
                c.drawImage(img, (tx - BLEED) * mm, (ty - BLEED) * mm,
                            (TRIM_W + 2 * BLEED) * mm, (TRIM_H + 2 * BLEED) * mm)
                c.restoreState()
        marks(c)
        c.setFont("Helvetica", 5)
        c.setFillColorCMYK(0, 0, 0, 1)
        side = "fata" if path.stem == "fata" else "verso"
        c.drawString(12.5 * mm, 315 * mm,
                     f"{NAME} A6 ({TRIM_W}x{TRIM_H}) x4 | SRA4 {SHEET_W}x{SHEET_H} | "
                     f"bleed {BLEED} mm | taiere comuna (cotor 0) | {side}")
        c.showPage()
    c.save()


def marks(c):
    """Semne de tăiere în afara zonei de bleed, ca la model."""
    c.setLineWidth(0.25)
    c.setStrokeColorCMYK(1, 1, 1, 1)
    xs = [X0 + i * TRIM_W for i in range(COLS + 1)]
    ys = [Y0 + i * TRIM_H for i in range(ROWS + 1)]
    for x in xs:
        c.line(x * mm, 1 * mm, x * mm, (Y0 - BLEED - 0.5) * mm)
        c.line(x * mm, (SHEET_H - Y0 + BLEED + 0.5) * mm, x * mm, (SHEET_H - 1) * mm)
    for y in ys:
        c.line(0.5 * mm, y * mm, (X0 - BLEED - 0.5) * mm, y * mm)
        c.line((SHEET_W - X0 + BLEED + 0.5) * mm, y * mm, (SHEET_W - 0.5) * mm, y * mm)


if __name__ == "__main__":
    build(HERE / "Rugaciune_A6_4up_SRA4_fata-verso.pdf")
    print("ok")
