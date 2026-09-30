#!/usr/bin/env python3
"""tts.py — Gemini TTS -> WAV. Utilizare: tts.py --voice Sulafat --text-file x.txt --out y.wav"""
import argparse, base64, json, os, sys, time, urllib.request, urllib.error, wave
ap=argparse.ArgumentParser()
ap.add_argument("--voice", required=True); ap.add_argument("--text-file", required=True)
ap.add_argument("--out", required=True); ap.add_argument("--style", default=""); ap.add_argument("--model", default="gemini-3.8-flash-tts")
a=ap.parse_args()
text=open(a.text_file,encoding="utf-8").read()
payload={"contents":[{"parts":[{"text":text}]}],
 "generationConfig":{"responseModalities":["AUDIO"],
  "speechConfig":{"voiceConfig":{"prebuiltVoiceConfig":{"voiceName":a.voice}}}}}
if a.style: payload["systemInstruction"]={"parts":[{"text":a.style}]}
url=f"https://generativelanguage.googleapis.com/v1beta/models/{a.model}:generateContent"
for attempt in range(5):
    try:
        req=urllib.request.Request(url,data=json.dumps(payload).encode(),method="POST",
            headers={"Content-Type":"application/json","x-goog-api-key":os.environ["GEMINI_API_KEY"]})
        res=json.loads(urllib.request.urlopen(req,timeout=600).read())
        break
    except urllib.error.HTTPError as e:
        body=e.read().decode()[:500]
        if e.code in (429,500,503) and attempt<4: time.sleep(2**attempt*2); continue
        sys.exit(f"HTTP {e.code}: {body}")
part=res["candidates"][0]["content"]["parts"][0]["inlineData"]
pcm=base64.b64decode(part["data"]); mime=part.get("mimeType","")
rate=int(mime.split("rate=")[1].split(";")[0]) if "rate=" in mime else 24000
if pcm[:4]==b"RIFF":
    open(a.out,"wb").write(pcm)
else:
    with wave.open(a.out,"wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
w=wave.open(a.out); print(a.out, f"{w.getnframes()/w.getframerate():.1f}s", w.getframerate(), mime)
