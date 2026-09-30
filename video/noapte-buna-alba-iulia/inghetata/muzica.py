import json,os,sys,urllib.request,base64
prompt,out=sys.argv[1],sys.argv[2]
p={"contents":[{"parts":[{"text":prompt}]}]}
req=urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/lyria-3.5:generateContent",data=json.dumps(p).encode(),headers={"Content-Type":"application/json","x-goog-api-key":os.environ["GEMINI_API_KEY"]})
r=json.loads(urllib.request.urlopen(req,timeout=900).read())
c=r["candidates"][0]
if "content" not in c: sys.exit("fara continut: "+json.dumps(c)[:400])
for part in c["content"]["parts"]:
    if "inlineData" in part: open(out,"wb").write(base64.b64decode(part["inlineData"]["data"])); print("saved",out)
