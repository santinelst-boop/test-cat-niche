#!/bin/bash
# genereaza toate cadrele, 3 in paralel
cd "$(dirname "$0")"; set -a; . ../.env; set +a
python3 - <<'PY'
import subprocess, os
from concurrent.futures import ThreadPoolExecutor
from cadre import SHOTS, STYLE, GIRL, BOY, DAD
def run(s):
    sid, refs, desc = s
    out=f"iesiri/{sid}.png"
    if os.path.exists(out): return sid+" exista"
    anchors=[]
    if any('fetita' in r for r in refs): anchors.append(GIRL)
    if any('sef' in r for r in refs): anchors.append(BOY)
    if any('tata' in r for r in refs): anchors.append(DAD)
    p = STYLE+"\n\nThe first image is the style reference."+(" The other images are character references." if refs else "")+"\n"+" ".join(anchors)+"\n\nScene: "+desc
    open(f"prompturi/{sid}.txt","w").write(p)
    cmd=["python3","nanobanana.py","--prompt-file",f"prompturi/{sid}.txt","--ref","referinte/stil_hartie.jpg"]
    for r in refs: cmd+=["--ref",r]
    cmd+=["--out",out,"--aspect","16:9","--size","2K"]
    r=subprocess.run(cmd,capture_output=True,text=True)
    return sid+": "+(r.stdout+r.stderr).strip().splitlines()[-1]
with ThreadPoolExecutor(3) as ex:
    for line in ex.map(run, SHOTS): print(line, flush=True)
PY
