# Agenda A5 2027 – Școala Gimnazială „1 Decembrie 1918” Alba Iulia

Copertă cartonată, montată **exact ca modelul Golden Silo** (`GoldenSilo_coperta_agenda_A5_2027_SRA3.pdf`).

| Fișier | Rol |
|---|---|
| `Agenda_A5_2027_coperta_SRA3_cu_semne.pdf` | **De tipar.** SRA3 orizontal, STÂNGA = FAȚĂ, DREAPTA = SPATE, cu semne de tăiere. |
| `sursa/coperta_agenda_a5_grafica.pdf` | Grafica originală (CorelDRAW, A5, fără bleed). |
| `build.py` | Scriptul care generează PDF-ul. |

## Cote (ca la Golden Silo)

- Coală: **SRA3 450 × 320 mm**, orizontal
- Carton: **148 × 210 mm**
- Întoarcere: **20 mm** pe fiecare latură → format tăiat **188 × 250 mm**
- Bleed: **3 mm** → 194 × 256 mm
- Semne de tăiere: 5 mm, 0,25 pt, registration
- Semne **negre** (100% K), 6 mm, 0,75 pt pe întoarcere: muchia cartonului și mijlocul (se ascund sub forzaț)

## Culoare

CMYK vectorial, profilul ICC din fișierul original. Galben C0 M25 Y85 K10, verde C95 M19 Y70 K72.
Fondul și liniile verzi sunt prelungite pe întoarcere și bleed.

## Interior (monocrom) – `interior/`

| Fișier | Rol |
|---|---|
| `interior/Agenda_A5_2027_interior_172pag_MONOCROM.pdf` | Interior A5, 172 pagini, monocrom. |
| `interior/Agenda_A5_2027_interior_172pag_MONOCROM_DUBLAJ_A4.pdf` | **De tipar.** Dublaj A4 identic cu Golden Silo (aceeași pagină A5 de 2 ori pe A4). |
| `interior/build_interior.py` | Scriptul care le generează din `interior/sursa/` (interiorul Golden Silo). |

- Datele Golden Silo înlocuite cu ale școlii: pag. 1 (prezentare + siglă), pag. 3 (siglă, CLASA / ȘCOALA
  în loc de FUNCȚIA / COMPANIA), antetul de pe pag. 5–172.
- Monocrom: tot în tonuri de negru; liniile au minimum 20% negru.
- Cotor: **+3 mm** față de Golden Silo (pag. impare mutate spre dreapta, pare spre stânga, fără scalare).
  Margine la cotor 15–17 mm, la exterior minimum 9 mm.
- Fonturi: Cinzel SemiBold și Cormorant Garamond Medium (SIL OFL, în `interior/fonts/`).
