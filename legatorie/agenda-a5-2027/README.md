# Agenda A5 2027 – Școala Gimnazială „1 Decembrie 1918” Alba Iulia

Coperți **cartonate cu spiră**: față și spate sunt două cartoane separate, fiecare îmbrăcat.

| Fișier | Rol |
|---|---|
| `Agenda_A5_2027_COPERTE_cartonat_spira_PRINT.pdf` | **De tipar.** 2 pagini: p.1 = FAȚĂ, p.2 = SPATE. Fără ghidaje. |
| `Agenda_A5_2027_COPERTE_verificare_ghidaje.pdf` | Doar pentru verificare: muchia cartonului, blocul A5, zona spirei. **Nu se tipărește.** |
| `sursa/coperta_agenda_a5_grafica.pdf` | Grafica originală (CorelDRAW, A5 fix, fără bleed). |
| `build.py` | Scriptul care generează PDF-urile (cotele se schimbă din constantele de sus). |

## Cote

- Bloc agendă: **148 × 210 mm** (A5)
- Carton: **152 × 216 mm** (+2 mm lățime, +3 mm înălțime față de bloc)
- Întoarcere (îmbrăcare) pe carton: **15 mm** pe fiecare latură
- Format fișier tipar: **182 × 246 mm** / pagină
- Spiră: zonă liberă de grafică importantă **12 mm** de la muchia cotorului
  (stânga pe față, dreapta pe spate privit din exterior). Perforare ghidaj: 3:1, pas 8,47 mm.

## Culoare

- CMYK, profil ICC păstrat din fișierul original; totul vectorial (text Arial încorporat).
- Galben fond: C0 M25 Y85 K10 · Verde linii/text: C95 M19 Y70 K72.
- Fondul și liniile verzi sunt prelungite pe toată întoarcerea; grafica e centrată pe carton.

## De confirmat cu legătoria

Dacă folosesc alt carton (ex. 150 × 216) sau altă întoarcere (ex. 18 mm), se modifică
`BOARD_W`, `BOARD_H`, `WRAP` în `build.py` și se rulează `python3 build.py`.
