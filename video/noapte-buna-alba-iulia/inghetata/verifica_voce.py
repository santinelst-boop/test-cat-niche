import base64,json,os,sys,urllib.request,re,difflib
from concurrent.futures import ThreadPoolExecutor
def norm(s): return re.sub(r"[^a-zăâîșțşţ0-9 ]"," ",s.lower().replace("ş","ș").replace("ţ","ț")).split()
def check(sid):
    b=base64.b64encode(open(f"audio/scene/{sid}.wav","rb").read()).decode()
    p={"contents":[{"parts":[{"text":"Transcrie exact, cuvânt cu cuvânt, ce se aude. Numerele scrie-le în litere. Doar transcrierea."},{"inline_data":{"mime_type":"audio/wav","data":b}}]}]}
    req=urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",data=json.dumps(p).encode(),headers={"Content-Type":"application/json","x-goog-api-key":os.environ["GEMINI_API_KEY"]})
    r=json.loads(urllib.request.urlopen(req,timeout=300).read())
    heard="".join(x.get("text","") for x in r["candidates"][0]["content"]["parts"])
    want=open(f"audio/scene/{sid}.txt").read().split("#### TRANSCRIPT")[-1]
    a,b2=norm(want),norm(heard)
    sm=difflib.SequenceMatcher(None,a,b2)
    diffs=[(op," ".join(a[i1:i2])," ".join(b2[j1:j2])) for op,i1,i2,j1,j2 in sm.get_opcodes() if op!="equal"]
    return sid, round(sm.ratio(),3), len(a), len(b2), diffs[:8]
ids=sys.argv[1:] or sorted(f[:-4] for f in os.listdir("audio/scene") if f.endswith(".wav"))
with ThreadPoolExecutor(5) as ex:
    for sid,ratio,na,nb,d in ex.map(check,ids): print(sid,ratio,na,nb,d)
