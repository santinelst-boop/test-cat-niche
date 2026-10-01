"""Pregătire copertă cartonată cu spiră, agendă A5 2027.

Fiecare copertă (față / spate) este un carton separat, îmbrăcat.
  bloc A5:        148 x 210 mm
  carton:         152 x 216 mm (2 mm depășire stânga/dreapta, 3 mm sus/jos)
  întoarcere:     15 mm pe fiecare latură (include grosimea cartonului)
  fișier final:   182 x 246 mm
Grafica originală rămâne vectorială și CMYK (ICC din CorelDRAW), centrată pe carton.
Fondul galben și liniile verzi sunt prelungite până la marginea întoarcerii.
"""
from pathlib import Path
import pikepdf
from pikepdf import Name, Dictionary, Array

MM = 72 / 25.4
TRIM_W, TRIM_H = 148, 210
BOARD_W, BOARD_H = 152, 216
WRAP = 15
PAGE_W, PAGE_H = BOARD_W + 2 * WRAP, BOARD_H + 2 * WRAP
OFF_X, OFF_Y = (PAGE_W - TRIM_W) / 2, (PAGE_H - TRIM_H) / 2

YELLOW = "0 0.2510 0.8510 0.1020"
GREEN = "0.9490 0.1882 0.7020 0.7216"
# liniile verzi din original (y jos/sus, în pt, coordonate PDF)
LINES = {0: [(71.7780, 74.6127)], 1: [(71.7780, 74.6127), (507.7860, 510.6206)]}

HERE = Path(__file__).parent
SRC = HERE / "sursa" / "coperta_agenda_a5_grafica.pdf"
NAMES = {0: "FATA", 1: "SPATE"}


def lines_for(i):
    """Liniile originale + verificare că poziția corespunde fișierului sursă."""
    return LINES[i]


def build(guides: bool):
    src = pikepdf.open(SRC)
    out = pikepdf.new()
    for i, sp in enumerate(src.pages):
        res = sp.Resources
        form = out.copy_foreign(sp.as_form_xobject())
        cs = out.copy_foreign(res.ColorSpace.CS14)
        gs = out.copy_foreign(res.ExtGState.GS13)
        W, H = PAGE_W * MM, PAGE_H * MM
        ox, oy = OFF_X * MM, OFF_Y * MM
        c = ["/GS0 gs /CS0 cs /CS0 CS", f"{YELLOW} scn 0 0 {W:.4f} {H:.4f} re f"]
        for y0, y1 in lines_for(i):
            c.append(f"{GREEN} scn {GREEN} SCN 0.5 w 0 {oy + y0:.4f} {W:.4f} {y1 - y0:.4f} re b")
        c.append(f"q 1 0 0 1 {ox:.4f} {oy:.4f} cm /Fx0 Do Q")
        if guides:
            c.append(guide_ops(i))
        page = out.add_blank_page(page_size=(W, H))
        page.Resources = Dictionary(
            XObject=Dictionary(Fx0=form),
            ColorSpace=Dictionary(CS0=cs),
            ExtGState=Dictionary(GS0=gs),
        )
        page.Contents = out.make_stream("\n".join(c).encode())
        page.TrimBox = Array([0, 0, W, H])
        page.BleedBox = Array([0, 0, W, H])
    return out


def guide_ops(i):
    """Ghidaje (doar în fișierul de verificare): carton, A5, zonă spiră."""
    m = MM
    bx, by = WRAP * m, WRAP * m
    ops = ["q 0 G 0.6 w [3 2] 0 d",
           f"{bx:.3f} {by:.3f} {BOARD_W*m:.3f} {BOARD_H*m:.3f} re S",  # muchie carton
           "1 0 1 RG [1 2] 0 d",
           f"{OFF_X*m:.3f} {OFF_Y*m:.3f} {TRIM_W*m:.3f} {TRIM_H*m:.3f} re S"]  # bloc A5
    # zona spiră: 12 mm de la muchia cotorului (stânga la față, dreapta la spate privit din exterior)
    sx = bx if i == 0 else bx + (BOARD_W - 12) * m
    ops += ["1 0 0 RG [] 0 d 0.4 w", f"{sx:.3f} {by:.3f} {12*m:.3f} {BOARD_H*m:.3f} re S"]
    hole_x = (WRAP + 6.5) * m if i == 0 else (WRAP + BOARD_W - 6.5) * m
    pitch = 8.47  # 3:1
    n = int((BOARD_H - 10) // pitch)
    start = WRAP + (BOARD_H - (n - 1) * pitch) / 2
    for k in range(n):
        y = (start + k * pitch) * m
        ops.append(f"{hole_x-2.5:.3f} {y-2.5:.3f} 5 5 re S")
    ops.append("Q")
    return "\n".join(ops)


if __name__ == "__main__":
    build(False).save(HERE / "Agenda_A5_2027_COPERTE_cartonat_spira_PRINT.pdf")
    build(True).save(HERE / "Agenda_A5_2027_COPERTE_verificare_ghidaje.pdf")
    print("ok", PAGE_W, "x", PAGE_H, "mm")
