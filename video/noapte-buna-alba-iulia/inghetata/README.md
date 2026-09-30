# Noapte bună, Alba Iulia — „Înghețata care n-a venit niciodată”

Film animat în stil teatru de hârtie decupată (~8 min), după scriptul audio din Notion
(„21 de scaune”, Ep. 1). Fluxul complet de producție, reutilizabil pentru celelalte povești.

## Unelte
- **Imagini:** Gemini 3 Pro Image (Nano Banana Pro), cu referințe de stil și de personaj — `nanobanana.py`
- **Voce:** Gemini 3.8 Flash TTS, vocea **Aoede** — `tts.py`
- **Muzică:** Lyria 3.5 (trei teme: cald / neliniștit / noapte) — `muzica.py`
- **Montaj:** Python + Pillow + numpy, codat cu ffmpeg — `monteaza.py`

Toate scripturile citesc cheia din variabila de mediu `GEMINI_API_KEY`. Cheia nu se pune în repo.

## Pași
1. `ghid-de-stil.md` — stilul, paleta și personajele.
2. Planșa de personaje (`referinte/plansa_personaje.jpg`), decupată în referințe separate
   (`fetita_portret.png`, `fetita_sezand.png`, `sef_portret.png`, `tata_portret.png`).
3. `cadre.py` — lista celor 24 de cadre (prompt + referințe); `genereaza.sh` le generează în `iesiri/`.
4. `audio/scene/*.txt` — narațiunea pe scene, cu antetul de regie din `audio/antet.txt`
   (fără antet, modelul TTS citește instrucțiunile cu voce tare).
   `tts.py --voice Aoede --text-file audio/scene/01_gradinita.txt --out audio/scene/01_gradinita.wav`
5. `verifica_voce.py` — transcrie fiecare scenă și o compară cu textul.
6. `muzica.py "<prompt>" audio/muzica_cald.mp3` (și `nelinistit`, `noapte`).
7. `monteaza.py` — timeline din duratele vocii, mișcări de cameră, cortină de teatru între scene,
   răcirea luminii pe parcursul poveștii, praf în lumina lămpii, granulație, titluri, mixaj cu ducking.
   Previzualizare: `python3 monteaza.py --scene 03_votul --fps 12`.
8. `subtitrare.py` — subtitrare română (.srt), aliniată pe pauzele din narațiune.

Imaginile generate, audio-ul și filmul final nu sunt în repo (sunt mari); se regenerează cu pașii de mai sus.
