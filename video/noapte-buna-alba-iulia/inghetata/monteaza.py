#!/usr/bin/env python3
"""monteaza.py — montajul video pentru „Înghețata care n-a venit niciodată”.

Citește narațiunea pe scene (audio/scene/*.wav), cadrele (iesiri/*.png) și muzica,
construiește timeline-ul, randează imaginea (mișcări de cameră, cortină de teatru între scene,
etalonare de culoare, praf în lumină, granulație, titluri) și mixează sunetul.

    python3 monteaza.py                 # tot filmul -> final/inghetata.mp4
    python3 monteaza.py --scene 03_votul --fps 12   # previzualizare rapidă a unei scene
"""
import argparse, json, math, os, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1920, 1080
SR = 48000
LEAD, TAIL = 1.6, 2.4          # secunde de tăcere înainte/după narațiunea fiecărei scene
CURTAIN = 0.9                  # durata închiderii/deschiderii cortinei
XFADE = 1.4                    # fondu între cadre în aceeași scenă
INK = np.array([24, 32, 54], np.float32)
FONT_HAND = "fonturi/caveat-600-normal.ttf"
FONT_TITLE = "fonturi/cormorant-garamond-600-italic.ttf"

# ---------------------------------------------------------------- timeline
# cold: 0 = lumina caldă originală, 1 = noapte rece. Mișcare: (zoom_start, zoom_end, (fx0,fy0), (fx1,fy1))
SCENES = [
 ("00_intro", "cald", [("00_titlu", 1, 0.00, (1.00, 1.08, (.5, .55), (.5, .50)))]),
 ("01_gradinita", "cald", [
    ("01a_sala", 3, 0.0, (1.02, 1.12, (.45, .55), (.40, .60))),
    ("01b_banuti", 2, 0.0, (1.15, 1.02, (.50, .55), (.50, .52))),
    ("01c_amintiri", 2, 0.0, (1.02, 1.12, (.50, .50), (.62, .40)))]),
 ("02_propunerea", "cald", [
    ("02a_propunerea", 2, 0.05, (1.00, 1.10, (.50, .55), (.52, .45))),
    ("02b_ura", 2, 0.05, (1.10, 1.00, (.50, .35), (.50, .50))),
    ("02c_craciun", 2, 0.08, (1.05, 1.20, (.40, .55), (.35, .45)))]),
 ("03_votul", "cald", [
    ("03a_foaia", 1, 0.15, (1.00, 1.12, (.50, .55), (.45, .50))),
    ("03b_votul", 3, 0.18, (1.00, 1.18, (.50, .45), (.35, .65))),
    ("03c_pantofii", 2, 0.18, (1.02, 1.12, (.45, .70), (.40, .75))),
    ("03b_votul", 1, 0.22, (1.18, 1.00, (.50, .40), (.50, .50)))]),
 ("04_asteptarea", "nelinistit", [
    ("04a_asteptarea", 3, 0.40, (1.00, 1.12, (.45, .50), (.45, .45))),
    ("04b_investitia", 3, 0.45, (1.02, 1.14, (.45, .55), (.72, .55)))]),
 ("05_cutia_goala", "nelinistit", [
    ("05a_cutia_goala", 2, 0.55, (1.00, 1.12, (.70, .60), (.75, .55))),
    ("05b_clasa_a_sasea", 2, 0.55, (1.12, 1.00, (.30, .45), (.40, .40))),
    ("05c_cat_de_tarziu", 2, 0.60, (1.00, 1.15, (.55, .55), (.50, .45)))]),
 ("06_ciclul", "nelinistit", [
    ("06a_sirul", 2, 0.65, (1.00, 1.10, (.55, .55), (.70, .50))),
    ("06b_numaratoarea", 2, 0.70, (1.05, 1.20, (.40, .60), (.20, .65)))]),
 ("07_ani_mai_tarziu", "noapte", [
    ("07a_anii", 2, 0.35, (1.00, 1.08, (.30, .55), (.70, .55))),
    ("07b_tatal", 3, 0.50, (1.00, 1.12, (.60, .55), (.70, .55))),
    ("07c_amintirea", 2, 0.50, (1.00, 1.15, (.40, .40), (.35, .35)))]),
 ("08_intrebarea", "noapte", [
    ("08a_dormitorul", 2, 0.25, (1.00, 1.12, (.50, .55), (.45, .55))),
    ("08b_soapta", 2, 0.25, (1.02, 1.15, (.60, .50), (.62, .45))),
    ("08c_tacerea", 2, 0.25, (1.00, 1.12, (.40, .50), (.40, .40))),
    ("08a_dormitorul", 1, 0.30, (1.12, 1.00, (.45, .55), (.50, .50)))]),
 ("09_outro", "noapte", [("09_final", 1, 0.30, (1.00, 1.12, (.50, .60), (.40, .70)))]),
]
WARM_SCENES = {"00_intro", "01_gradinita", "02_propunerea", "03_votul"}
# text pictat direct pe imagine, în coordonatele cadrului (x, y, lățime, unghi)
STAMPS = {"01b_banuti": [("BANII NOȘTRI", 1380, 1110, 470, -3)]}


def wav_len(p):
    with wave.open(p) as w:
        return w.getnframes() / w.getframerate()


def narration_len(sid):
    p = f"audio/scene/{sid}.wav"
    if os.path.exists(p):
        return wav_len(p)
    txt = open(f"audio/scene/{sid}.txt", encoding="utf-8").read().split("#### TRANSCRIPT")[-1]
    return len(txt) / 11.0   # estimare pentru previzualizare fără voce


def build_timeline():
    t, scenes = 0.0, []
    for sid, cue, shots in SCENES:
        dur = LEAD + narration_len(sid) + TAIL
        wsum = sum(s[1] for s in shots)
        # cadrele se suprapun XFADE secunde; distribuim durata pe ponderi
        usable = dur + XFADE * (len(shots) - 1)
        out, st = [], t
        for img, wgt, cold, move in shots:
            d = usable * wgt / wsum
            out.append(dict(img=img, start=st, dur=d, cold=cold, move=move))
            st += d - XFADE
        scenes.append(dict(id=sid, cue=cue, start=t, dur=dur, narr_start=t + LEAD, shots=out))
        t += dur
    return scenes, t


# ---------------------------------------------------------------- imagine
def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def grade(im, cold):
    a = np.asarray(im, np.float32)
    if cold > 0:
        # răcire: scade roșul și verdele, ridică albastrul, coboară luminozitatea, desaturează ușor
        lum = a.mean(axis=2, keepdims=True)
        a = a * (1 - 0.25 * cold) + lum * 0.25 * cold
        a *= np.array([1 - 0.22 * cold, 1 - 0.10 * cold, 1 + 0.10 * cold], np.float32)
        a *= 1 - 0.28 * cold
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def stamp(im, sid):
    for text, cx, cy, width, angle in STAMPS.get(sid, []):
        size = 200
        font = ImageFont.truetype(FONT_HAND, size)
        while font.getlength(text) > width:
            size -= 4
            font = ImageFont.truetype(FONT_HAND, size)
        layer = Image.new("RGBA", (int(width * 1.3), size * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.text((layer.width / 2, layer.height / 2), text, font=font, fill=(58, 36, 28, 215), anchor="mm")
        layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
        im.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))
    return im


_cache = {}


def shot_image(img, cold):
    key = (img, round(cold, 3))
    if key not in _cache:
        if len(_cache) > 6:
            _cache.pop(next(iter(_cache)))
        im = Image.open(f"iesiri/{img}.png").convert("RGBA")
        im = stamp(im, img).convert("RGB")
        _cache[key] = grade(im, cold)
    return _cache[key]


def camera(im, move, u):
    z0, z1, c0, c1 = move
    e = ease(u)
    z = z0 + (z1 - z0) * e
    fx = c0[0] + (c1[0] - c0[0]) * e
    fy = c0[1] + (c1[1] - c0[1]) * e
    iw, ih = im.size
    ch = ih / z
    cw = ch * W / H
    if cw > iw:
        cw = iw; ch = cw * H / W
    x0 = min(max(fx * iw - cw / 2, 0), iw - cw)
    y0 = min(max(fy * ih - ch / 2, 0), ih - ch)
    return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))


def make_static():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    vig = (1 - 0.32 * np.clip(r - 0.35, 0, 1) ** 1.6)[..., None]
    rng = np.random.default_rng(7)
    grain = [(rng.normal(0, 2.2, (H // 2, W // 2))).astype(np.float32) for _ in range(6)]
    grain = [np.kron(g, np.ones((2, 2), np.float32))[..., None] for g in grain]
    # textura cortinei: carton albastru cu fibre
    tex = rng.normal(0, 1, (H, W // 2)).astype(np.float32)
    tex = np.asarray(Image.fromarray(((tex * 20) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) - 128
    curtain = np.clip(INK + tex[..., None] * 0.35, 0, 255)
    sprite = np.exp(-((np.mgrid[-8:9, -8:9] ** 2).sum(0)) / 18.0).astype(np.float32)[..., None]
    return vig, grain, curtain, sprite


def text_layer(lines):
    """lines: [(text, font_path, size, y, rgba)] -> RGBA pe tot cadrul"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for text, fp, size, y, col in lines:
        f = ImageFont.truetype(fp, size)
        d.text((W / 2 + 3, y + 4), text, font=f, fill=(10, 12, 25, 120), anchor="mm")
        d.text((W / 2, y), text, font=f, fill=col, anchor="mm")
    return np.asarray(im, np.float32)


def overlays(total):
    cream = (246, 236, 214, 255)
    pink = (238, 190, 196, 255)
    return [
        # (start, end, layer)
        (1.2, 9.5, text_layer([
            ("Noapte bună, Alba Iulia", FONT_HAND, 64, 180, pink),
            ("Înghețata care n-a venit niciodată", FONT_TITLE, 104, 290, cream),
            ("21 de scaune · Episodul 1", FONT_HAND, 46, 385, cream)])),
        (total - 9.0, total - 0.8, text_layer([
            ("Noapte bună, Alba Iulia.", FONT_TITLE, 92, 470, cream),
            ("albaiulia.report", FONT_HAND, 54, 570, pink)])),
    ]


def render_chunk(args):
    idx, f0, f1, fps, scenes, total, out = args
    vig, grain, curtain, sprite = make_static()
    ovs = overlays(total)
    rng = np.random.default_rng(100 + idx)
    dust = rng.random((36, 4)).astype(np.float32)  # x, y, viteză, fază
    proc = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                             "-crf", "20", "-tune", "film", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        t = fi / fps
        sc = next((s for s in scenes if s["start"] <= t < s["start"] + s["dur"]), scenes[-1])
        # cadrele active (maxim două, în fondu)
        acc, wsum = None, 0.0
        for sh in sc["shots"]:
            if sh["start"] - 1e-6 <= t < sh["start"] + sh["dur"]:
                a = 1.0
                if t < sh["start"] + XFADE and sh is not sc["shots"][0]:
                    a = ease((t - sh["start"]) / XFADE)
                frame = np.asarray(camera(shot_image(sh["img"], sh["cold"]), sh["move"], (t - sh["start"]) / sh["dur"]), np.float32)
                if acc is None:
                    acc = frame
                else:
                    acc = acc * (1 - a) + frame * a
        if acc is None:
            acc = np.zeros((H, W, 3), np.float32)
        # pâlpâirea lămpii în scenele calde
        if sc["id"] in WARM_SCENES:
            acc *= 1 + 0.012 * math.sin(t * 7.3) * math.sin(t * 2.1 + 1)
            # praf în lumină
            for k, (x, y, v, ph) in enumerate(dust):
                px = int(((x + 0.004 * t * (0.5 + v)) % 1) * W)
                py = int(((y - 0.010 * t * (0.3 + v)) % 1) * H)
                br = 14 * (0.5 + 0.5 * math.sin(t * (0.7 + v) + ph * 6))
                if 8 <= px < W - 9 and 8 <= py < H - 9:
                    acc[py - 8:py + 9, px - 8:px + 9] += sprite * br * np.array([1.0, 0.9, 0.7], np.float32)
        acc = acc * vig + grain[(fi // 4) % 6]
        # titluri
        for s0, s1, layer in ovs:
            if s0 <= t < s1:
                a = min(ease((t - s0) / 1.5), ease((s1 - t) / 1.5))
                al = layer[..., 3:4] / 255 * a
                acc = acc * (1 - al) + layer[..., :3] * al
        # cortina: se închide la sfârșitul scenei, se deschide la început
        ts = t - sc["start"]
        close = 0.0
        if ts < CURTAIN and sc is not scenes[0]:
            close = 1 - ease(ts / CURTAIN)
        elif sc["dur"] - ts < CURTAIN and sc is not scenes[-1]:
            close = ease(1 - (sc["dur"] - ts) / CURTAIN)
        if sc is scenes[0] and ts < 1.2:
            close = 1 - ease(ts / 1.2)
        if sc is scenes[-1] and sc["dur"] - ts < 1.0:
            acc *= ease((sc["dur"] - ts) / 1.0)
        if close > 0:
            half = int(close * W / 2)
            if half > 0:
                acc[:, :half] = curtain[:, -half:]
                acc[:, W - half:] = curtain[:, :half]
                # umbră moale la marginea cortinei
                for edge, sign in ((half, 1), (W - half, -1)):
                    for k in range(1, 28):
                        c = edge + sign * k - (1 if sign < 0 else 0)
                        if 0 <= c < W:
                            acc[:, c] *= 1 - 0.45 * (1 - k / 28)
        proc.stdin.write(np.clip(acc, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()
    return out


# ---------------------------------------------------------------- sunet
def load_audio(path):
    raw = subprocess.run([FFMPEG, "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def sfx_clock(n):
    out = np.zeros(n, np.float32)
    tick = np.exp(-np.arange(int(0.03 * SR)) / (0.004 * SR)) * np.random.default_rng(1).normal(0, 1, int(0.03 * SR))
    for i, s in enumerate(range(0, n - len(tick), SR)):
        out[s:s + len(tick)] += tick * (0.10 if i % 2 else 0.07)
    return out


def sfx_crickets(n):
    t = np.arange(n) / SR
    env = (np.sin(2 * np.pi * 14 * t) > 0.3).astype(np.float32) * (np.sin(2 * np.pi * 0.45 * t) > 0).astype(np.float32)
    env = np.convolve(env, np.ones(200) / 200, "same")
    return (np.sin(2 * np.pi * 4300 * t) * env * 0.012).astype(np.float32)


def sfx_paper(n):
    rng = np.random.default_rng(3)
    x = rng.normal(0, 1, n).astype(np.float32)
    x = x - np.convolve(x, np.ones(6) / 6, "same")      # trece-sus: foșnet
    env = np.exp(-((np.arange(n) - n / 2) / (n / 5)) ** 2) * (0.5 + 0.5 * np.abs(np.sin(np.arange(n) / 900)))
    return (x * env * 0.06).astype(np.float32)


def mix(scenes, total, out):
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    active = np.zeros(n, np.float32)
    for sc in scenes:
        p = f"audio/scene/{sc['id']}.wav"
        if os.path.exists(p):
            v = load_audio(p)
            s = int(sc["narr_start"] * SR)
            voice[s:s + len(v)] += v[:n - s]
            active[s:s + len(v)] = 1
    # ducking: muzica scade cât vorbește naratoarea
    k = int(0.6 * SR)
    cs = np.concatenate([[0], np.cumsum(active)])
    idx = np.arange(n)
    duck = ((cs[np.minimum(idx + k // 2, n)] - cs[np.maximum(idx - k // 2, 0)]) / k).astype(np.float32)
    music = np.zeros(n, np.float32)
    cues = {c: load_audio(f"audio/muzica_{c}.mp3") for c in ("cald", "nelinistit", "noapte")}
    groups = []
    for sc in scenes:
        if groups and groups[-1][0] == sc["cue"]:
            groups[-1][2] = sc["start"] + sc["dur"]
        else:
            groups.append([sc["cue"], sc["start"], sc["start"] + sc["dur"]])
    fade = int(3 * SR)
    for cue, a, b in groups:
        src = cues[cue]
        s, e = int(a * SR), min(int(b * SR) + fade, n)
        L = e - s
        seg = np.tile(src, L // len(src) + 1)[:L].copy()
        env = np.ones(L, np.float32)
        env[:fade] = np.linspace(0, 1, fade)
        env[-fade:] = np.linspace(1, 0, fade)
        music[s:e] += seg * env
    music *= 0.30 - 0.19 * duck
    sfx = np.zeros(n, np.float32)
    for sc in scenes:
        s, e = int(sc["start"] * SR), int((sc["start"] + sc["dur"]) * SR)
        if sc["id"] in ("04_asteptarea", "05_cutia_goala"):
            sfx[s:e] += sfx_clock(e - s)
        if sc["id"] in ("06_ciclul", "08_intrebarea", "09_outro"):
            sfx[s:e] += sfx_crickets(e - s)
        if sc is not scenes[0]:
            m = int(1.8 * SR)
            c = s - m // 2
            sfx[max(c, 0):c + m] += sfx_paper(m)[:max(0, min(m, n - c))][-len(sfx[max(c, 0):c + m]):]
    master = voice * 1.0 + music + sfx
    master /= max(1.0, np.abs(master).max() / 0.95)
    st = np.stack([master, master], 1)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_s16le", out], input=st.astype(np.float32).tobytes(), check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--scene", help="randează doar o scenă (previzualizare)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="final/inghetata.mp4")
    a = ap.parse_args()
    scenes, total = build_timeline()
    os.makedirs("final/tmp", exist_ok=True)
    json.dump(scenes, open("final/timeline.json", "w"), indent=1, ensure_ascii=False)
    t0, t1 = 0.0, total
    if a.scene:
        sc = next(s for s in scenes if s["id"] == a.scene)
        t0, t1 = sc["start"], sc["start"] + sc["dur"]
    f0, f1 = int(t0 * a.fps), int(t1 * a.fps)
    print(f"durată totală {total/60:.1f} min; randez {t0:.1f}–{t1:.1f}s = {f1-f0} cadre")
    step = math.ceil((f1 - f0) / a.workers)
    jobs = [(i, f0 + i * step, min(f1, f0 + (i + 1) * step), a.fps, scenes, total, f"final/tmp/part{i}.mp4")
            for i in range(a.workers) if f0 + i * step < f1]
    with Pool(len(jobs)) as p:
        parts = p.map(render_chunk, jobs)
    with open("final/tmp/list.txt", "w") as f:
        f.writelines(f"file '{os.path.basename(x)}'\n" for x in parts)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "final/tmp/list.txt",
                    "-c", "copy", "final/tmp/video.mp4"], check=True)
    mix(scenes, total, "final/tmp/audio.wav")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", "final/tmp/video.mp4", "-ss", f"{t0:.3f}", "-t", f"{t1-t0:.3f}",
                    "-i", "final/tmp/audio.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", a.out], check=True)
    print("gata:", a.out)


if __name__ == "__main__":
    main()
