#!/usr/bin/env python3
"""
nanobanana.py — generare de imagini cu Gemini (Nano Banana Pro) folosind
referinte de caracter la rezolutie plina, cu salvare directa pe disc.

Ocoleste cele doua limite ale MCP-ului Nano-Banana:
  1. plafonul de ~4096 caractere base64 pentru TOATE referintele la un loc
  2. faptul ca GENERATE_IMAGE_WITH_REFS returneaza doar inline, nesalvabil

Utilizare:
    export GEMINI_API_KEY=...
    python3 nanobanana.py \
        --prompt "..." \
        --ref referinte/posy_portret.png --ref referinte/posy_color.png \
        --out iesiri/posy_balta.png \
        --aspect 4:5 --size 2K

    # prompt dintr-un fisier, mai comod pentru texte lungi
    python3 nanobanana.py --prompt-file prompt.txt --ref r1.png --out o.png
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-3-pro-image-preview"
MAX_REFS = 14

ASPECTS = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
SIZES = {"1K", "2K", "4K"}


def load_ref(path: Path) -> dict:
    """Citeste o imagine de referinta la rezolutie plina, fara downscale."""
    if not path.is_file():
        sys.exit(f"[eroare] referinta lipseste: {path}")
    mime = mimetypes.guess_type(path.name)[0]
    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        sys.exit(f"[eroare] format nesuportat pentru {path} (foloseste png/jpg/webp)")
    data = path.read_bytes()
    print(f"  ref {path.name}: {len(data)/1024:.0f} KB, {mime}")
    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}}


def build_payload(prompt: str, refs: list[Path], aspect: str, size: str) -> dict:
    parts = [{"text": prompt}] + [load_ref(p) for p in refs]
    return {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect, "imageSize": size},
        },
    }


def call_api(model: str, payload: dict, api_key: str, timeout: int) -> dict:
    url = f"{API_ROOT}/{model}:generateContent"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def extract_images(result: dict) -> list[tuple[bytes, str]]:
    out = []
    for cand in result.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                mime = blob.get("mimeType") or blob.get("mime_type") or "image/png"
                out.append((base64.b64decode(blob["data"]), mime))
            elif part.get("text"):
                print(f"  [model] {part['text'][:400]}")
    return out


def save(images: list[tuple[bytes, str]], out: Path) -> list[Path]:
    out.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for i, (data, mime) in enumerate(images):
        ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(mime, ".png")
        target = out if len(images) == 1 else out.with_name(f"{out.stem}_{i+1}{ext}")
        if len(images) == 1 and target.suffix.lower() not in {ext, ".png", ".jpg", ".jpeg"}:
            target = target.with_suffix(ext)
        target.write_bytes(data)
        print(f"  -> {target}  ({len(data)/1024:.0f} KB)")
        written.append(target)
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description="Gemini image generation cu referinte de caracter")
    ap.add_argument("--prompt", help="promptul de generare")
    ap.add_argument("--prompt-file", type=Path, help="fisier text cu promptul")
    ap.add_argument("--ref", action="append", type=Path, default=[],
                    help=f"imagine de referinta (repetabil, max {MAX_REFS})")
    ap.add_argument("--out", type=Path, required=True, help="calea fisierului de iesire")
    ap.add_argument("--aspect", default="1:1", choices=sorted(ASPECTS))
    ap.add_argument("--size", default="2K", choices=sorted(SIZES))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--n", type=int, default=1, help="cate variante sa genereze")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--retries", type=int, default=4)
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.exit("[eroare] lipseste GEMINI_API_KEY in mediu")

    if args.prompt_file:
        prompt = args.prompt_file.read_text(encoding="utf-8").strip()
    elif args.prompt:
        prompt = args.prompt
    else:
        sys.exit("[eroare] da --prompt sau --prompt-file")

    if len(args.ref) > MAX_REFS:
        sys.exit(f"[eroare] maxim {MAX_REFS} referinte")

    print(f"model {args.model} | {args.aspect} | {args.size} | {len(args.ref)} referinte")
    payload = build_payload(prompt, args.ref, args.aspect, args.size)

    for n in range(args.n):
        target = args.out if args.n == 1 else args.out.with_name(f"{args.out.stem}_v{n+1}{args.out.suffix}")
        delay = 1.0
        for attempt in range(args.retries):
            try:
                result = call_api(args.model, payload, api_key, args.timeout)
                images = extract_images(result)
                if not images:
                    fr = (result.get("candidates") or [{}])[0].get("finishReason")
                    print(f"  [atentie] niciun output (finishReason={fr})")
                    break
                save(images, target)
                break
            except urllib.error.HTTPError as e:
                body = e.read().decode()[:600]
                if e.code in (429, 500, 503) and attempt < args.retries - 1:
                    print(f"  [retry {attempt+1}] HTTP {e.code}, astept {delay:.0f}s")
                    time.sleep(delay)
                    delay *= 2
                    continue
                sys.exit(f"[eroare] HTTP {e.code}: {body}")
            except Exception as e:  # noqa: BLE001
                if attempt < args.retries - 1:
                    print(f"  [retry {attempt+1}] {e}")
                    time.sleep(delay)
                    delay *= 2
                    continue
                sys.exit(f"[eroare] {e}")


if __name__ == "__main__":
    main()
