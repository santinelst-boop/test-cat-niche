import json, wave, re, numpy as np
sc = json.load(open("final/timeline.json"))
def ts(t):
    h,m=int(t//3600),int(t%3600//60); s=t%60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int((s-int(s))*1000):03d}"
def speech_runs(path, min_gap=0.45):
    w=wave.open(path); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)
    hop=int(sr*0.02); e=np.array([np.sqrt((x[i:i+hop]**2).mean()) for i in range(0,len(x)-hop,hop)])
    on=e>max(200,e.max()*0.04); runs=[]; start=None; last=None
    for i,v in enumerate(on):
        t=i*0.02
        if v:
            if start is None: start=t
            elif t-last>min_gap: runs.append([start,last+0.02]); start=t
            last=t
    if start is not None: runs.append([start,last+0.02])
    return runs
out=[]; n=1; mism=[]
for s in sc:
    txt=open(f"audio/scene/{s['id']}.txt",encoding="utf-8").read().split("#### TRANSCRIPT")[-1]
    body=re.sub(r"\s+"," ",txt).strip()
    paras=[p.strip() for p in re.split(r"(?<=[.?!])\s+(?=[—A-ZĂÂÎȘȚ])", body) if p.strip() and p.strip(". ")]
    runs=speech_runs(f"audio/scene/{s['id']}.wav", min_gap=0.25)
    gaps=[((runs[i][1]+runs[i+1][0])/2, runs[i+1][0]-runs[i][1]) for i in range(len(runs)-1)]
    A,B=runs[0][0],runs[-1][1]; tot=sum(len(p) for p in paras); acc=0; bounds=[A]; used=set()
    for p in paras[:-1]:
        acc+=len(p); exp=A+(B-A)*acc/tot
        cand=[(abs(g-exp)-0.3*d,i) for i,(g,d) in enumerate(gaps) if i not in used and g>bounds[-1] and abs(g-exp)<4]
        if cand: _,i=min(cand); used.add(i); bounds.append(gaps[i][0])
        else: bounds.append(max(exp,bounds[-1]+0.5))
    bounds.append(B)
    runs=[[bounds[i],bounds[i+1]] for i in range(len(paras))]
    for p,(a,b) in zip(paras,runs):
        # rânduri de max ~42 caractere
        words=p.split(); lines=[""]
        for w_ in words:
            if len(lines[-1])+len(w_)+1>42 and lines[-1]: lines.append(w_)
            else: lines[-1]=(lines[-1]+" "+w_).strip()
        chunks=["\n".join(lines[i:i+2]) for i in range(0,len(lines),2)]
        tot=sum(len(c) for c in chunks); t=a
        for c in chunks:
            d=(b-a)*len(c)/tot
            out.append(f"{n}\n{ts(s['narr_start']+t)} --> {ts(s['narr_start']+t+d-0.05)}\n{c}\n"); n+=1; t+=d
open("final/inghetata-care-n-a-venit-niciodata.ro.srt","w",encoding="utf-8").write("\n".join(out))
print(n-1,'subtitrări')
