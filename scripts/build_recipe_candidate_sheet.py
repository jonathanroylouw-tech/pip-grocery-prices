#!/usr/bin/env python3
"""Source and rank candidate *real* meal photos for all 82 PIP dishes.
Produce local offline approval mosaics and explicit CC attribution records.
No generic fallback to another dish and no AI-generated images.
"""
import concurrent.futures,io,re,ast,json,os,math,time,statistics,hashlib,threading
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageStat,ImageFilter,ImageChops
from pathlib import Path
import requests
SOURCE=Path("scripts/build_recipe_photo_contact_sheet.py").read_text()
tree=ast.parse(SOURCE)
params={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ("NAMES","SEARCH"):
        params[node.targets[0].id]=ast.literal_eval(node.value)
NAMES=params["NAMES"]; QUERIES=params["SEARCH"]
assert len(NAMES)==82==len(QUERIES)
OUT=Path("previews/curated"); OUT.mkdir(parents=True,exist_ok=True)
HDR={"User-Agent":"PIP Research Photo Board/1.1 (contact via Github source)"}
BAD=("vector","artwork","illustration","anime","sticker","poster","book cover","menu","hand drawing","logo","3d render","drawing","painting","screenshot","collage","food packaging","uncooked","raw meat","logo")
STOP={"and","with","style","roasted","home","homemade","mild","easy","classic","warm","hearty","in","on","&","of","style","inspired","south","african","fresh","sauce","bowl","recipe","served","plate"}
SYN={"fries":["chips","fries"],"chips":["fries","chips"],"beef":["beef","steak","meat","mince","ground"],"chicken":["chicken","poultry"],"potatoes":["potato","potatoes"],"vegetable":["vegetables","veggie","vegetable"],"beans":["beans","bean"],"fish":["fish","hake"],"tuna":["tuna"],"curry":["curry"],"lentil":["lentils","lentil"],"eggs":["egg","eggs"],"wrap":["wrap","wraps","tortilla"],"pizza":["pizza"],"pasta":["pasta"],"noodle":["noodles","noodle"],"soup":["soup"],"lasagne":["lasagne","lasagna"],"bobotie":["bobotie"],"koftas":["kofta","koftas"],"shakshuka":["shakshuka"],"couscous":["couscous"],"schnitzel":["schnitzel"],"risotto":["risotto"],"moussaka":["moussaka"],"tacos":["taco","tacos"],"taco":["taco","tacos"],"pap":["pap","mealie"],"boerewors":["boerewors","sausage"],"frittata":["frittata"],"stew":["stew"],"chilli":["chili","chilli"],"chili":["chili","chilli"],"biryani":["biryani"],"gnocchi":["gnocchi"],"fried":["fried"],"baked":["baked"],"butternut":["butternut","squash"],"hake":["hake","fish"]}
SESH=requests.Session(); SESH.headers.update(HDR)
_api_lock=threading.Lock()
_next_api=[0.0]
def paced_get(url,params):
    for attempt in range(5):
        with _api_lock:
            wait=max(0,_next_api[0]-time.monotonic())
            if wait:time.sleep(wait)
            _next_api[0]=time.monotonic()+1.1
        try:
            r=requests.get(url,params=params,timeout=16,headers=HDR)
            if r.status_code in (429,403,503):
                print("API_RETRY",r.status_code,url.split("/")[2],flush=True)
                time.sleep(min(15,2+3*attempt))
                continue
            return r
        except Exception as e:
            print("API_EXC",str(e)[:70],flush=True)
            time.sleep(1+attempt)
    return None
def tokens(s):
    return [w for w in re.findall(r"[a-zA-Z]{3,}",s.lower()) if w not in STOP]
def meaning_score(p,q):
    title=(p.get("title") or "").lower()
    raw_tags=p.get("tags") or []
    tags=" ".join(t.get("name","") for t in raw_tags if isinstance(t,dict)).lower()
    pool=title+" "+tags[:800]
    if any(w in pool for w in BAD):return -99
    ts=tokens(q)
    if not ts:return 0
    score=0
    for t in ts:
        opts=SYN.get(t,[t])
        if any(o in title for o in opts): score+=3.5
        elif any(o in tags for o in opts): score+=1.7
    if not any((o in pool) for t in ts for o in SYN.get(t,[t])):return -99
    if len(ts)==1 and not any(w in title for w in SYN.get(ts[0],[ts[0]])):score-=2
    size=min(int(p.get("width") or 0),int(p.get("height") or 0))
    if size>=900:score+=2.6
    elif size>=600:score+=1.8
    elif size>=350:score+=0.8
    elif size<200:score-=5
    if p.get("provider")=="commons": score+=1.1
    if p.get("provider")=="flickr":score+=0.5
    return score
def download_img(u):
    if not u:return None
    try:
        r=requests.get(u,timeout=9,headers=HDR)
        if r.status_code!=200 or len(r.content)<9000 or len(r.content)>6_000_000:return None
        img=Image.open(io.BytesIO(r.content));img.load()
        if img.width<250 or img.height<170:return None
        return img.convert("RGB")
    except Exception:return None
def eval_photo(im):
    sm=ImageOps.fit(im,(144,96))
    stats=ImageStat.Stat(sm)
    bright=sum(stats.mean)/3
    hsv=sm.convert("HSV")
    sat=ImageStat.Stat(hsv).mean[1]
    entropy=sm.convert("L").entropy()
    cont=ImageStat.Stat(sm.convert("L")).stddev[0]
    warm=sum(1 for r,g,b in sm.resize((72,48)).getdata() if r>g*1.1 and r>b*1.1)/3456
    score= min(3.1,entropy*0.38)+min(2.5,sat/40)+min(2.5,cont/18)+min(warm*6,0.7)
    if bright<55 or bright>216:score-=5
    elif bright<80 or bright>190:score-=2.4
    if sat<20:score-=2.2
    if cont<22:score-=2.5
    return score

def openverse(q):
    items=[]
    try:
        r=paced_get("https://api.openverse.org/v1/images/",{"q":q,"page_size":25,"license":"cc0,pdm,by,by-sa","mature":"false"})
        if r is None or not r.ok:return items
        for p in r.json().get("results",[]):
            if p.get("license") not in ("cc0","pdm","by","by-sa"):continue
            items.append({"provider":p.get("source") or "openverse","title":p.get("title") or "","tags":p.get("tags") or [],"url":p.get("thumbnail") or p.get("url"),"original":p.get("url"),"page":p.get("foreign_landing_url"),"creator":p.get("creator"),"license":p.get("license"),"width":p.get("width"),"height":p.get("height")})
    except Exception:pass
    return items
def commons(q):
    data=[]
    try:
        resp=paced_get("https://commons.wikimedia.org/w/api.php",{"action":"query","generator":"search","gsrsearch":q+" food","gsrnamespace":6,"gsrlimit":12,"prop":"imageinfo","iiprop":"url|size|extmetadata","iiurlwidth":"700","format":"json"})
        if resp is None or not resp.ok:return data
        for item in resp.json().get("query",{}).get("pages",{}).values():
            a=(item.get("imageinfo") or [{}])[0]
            mt=a.get("mime") or ""
            if not re.search(r"\.(jpe?g|png|webp)(\?|$)",a.get("url",""),re.I):continue
            l=(a.get("extmetadata",{}).get("LicenseShortName",{}) or {}).get("value","")
            # Commons photos: keep only licence types appropriate to preview/commercial reuse
            if not any(x in l.lower() for x in ("cc by","cc0","public domain","pd-","cc-by")):continue
            title=item.get("title","").removeprefix("File:")
            data.append({"provider":"commons","title":title,"tags":[],"url":a.get("thumburl") or a.get("url"),"original":a.get("url"),"page":a.get("descriptionurl"),"creator":re.sub("<[^>]*>","",a.get("extmetadata",{}).get("Artist",{}).get("value",""))[:100],"license":l,"width":a.get("width"),"height":a.get("height")})
    except Exception:pass
    return data

def task(i):
    q=QUERIES[i]
    qs=[q]
    important=tokens(q)
    if len(important)>2: qs.append(" ".join(important[:2]))
    result={}
    for query in qs:
        for p in openverse(query):
            u=p["url"]
            if u and u not in result:result[u]=p
    for p in commons(q):
        u=p["url"]
        if u and u not in result:result[u]=p
    order=sorted(result.values(),key=lambda p:meaning_score(p,q),reverse=True)
    options=[]
    for p in order[:11]:
        ms=meaning_score(p,q)
        if ms<=0:continue
        im=download_img(p["url"])
        if im is None:continue
        photoscore=eval_photo(im)
        s=ms+photoscore
        if s<1:continue
        p["match_score"]=round(ms,1);p["visual_score"]=round(photoscore,1);p["final_score"]=round(s,1)
        p["query"]=q;p["recipe"]=NAMES[i];p["recipe_no"]=i+1
        options.append((s,im,p))
    options.sort(reverse=True,key=lambda x:x[0])
    result=[]
    seen=set()
    for s,im,p in options:
        thumb=ImageOps.fit(im,(225,147),method=Image.Resampling.LANCZOS)
        sig=hashlib.md5(thumb.resize((20,14)).tobytes()).hexdigest()[:14]
        if sig in seen:continue
        seen.add(sig)
        result.append((thumb,p))
        if len(result)>=3:break
    return i,result
def fnt(size,bold=False):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        if Path(f).exists():return ImageFont.truetype(f,size)
    return ImageFont.load_default()
print("Beginning 82 multi-source photo searches",flush=True)
ROWS_PER_PAGE=21
results=[None]*82
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    future={ex.submit(task,i):i for i in range(82)}
    for t in concurrent.futures.as_completed(future):
        try:i,found=t.result()
        except Exception as e:i=future[t];found=[];print("SEARCH ERROR",i,str(e),flush=True)
        results[i]=found
        if sum(x is not None for x in results)%10==0:print("Finished",sum(x is not None for x in results),"/82",flush=True)
manifest=[]
for page in range(math.ceil(82/ROWS_PER_PAGE)):
    ids=list(range(page*ROWS_PER_PAGE,min((page+1)*ROWS_PER_PAGE,82)))
    W=1060;H=100+len(ids)*184
    board=Image.new("RGB",(W,H),"#101717")
    dr=ImageDraw.Draw(board)
    dr.text((22,18),f"PIP  /  REAL FOOD PHOTO CANDIDATES — PAGE {page+1}",font=fnt(25,True),fill="#FFFFFF")
    dr.text((23,55),"Each recipe has up to 3 independently sourced candidates. Review before use.",font=fnt(14),fill="#BEC8C0")
    for row,i in enumerate(ids):
        y=90+184*row
        dr.rectangle((5,y,1055,y+179),fill=("#182020" if row%2 else "#202827"))
        title=NAMES[i]
        dr.text((14,y+17),str(i+1).zfill(2),font=fnt(15,True),fill="#A4B8AC")
        # split name to 2 lines if needed
        words=title.split(" ");lines=[];current=""
        for w in words:
            tmp=(current+" "+w).strip()
            if dr.textbbox((0,0),tmp,font=fnt(13,True))[2]>280 and current:
                lines.append(current);current=w
            else:current=tmp
        if current:lines.append(current)
        for k,line in enumerate(lines[:3]):dr.text((14,y+49+k*20),line,font=fnt(13,True),fill="#FFFFFF")
        photos=results[i] or []
        entry={"recipe_no":i+1,"recipe":title,"search":QUERIES[i],"candidates":[]}
        for k,(im,p) in enumerate(photos):
            x=315+k*246
            board.paste(im,(x,y+6))
            dr.text((x,y+156),f"{'ABC'[k]}  ·  score {p['final_score']:.1f}  ·  {p['provider'][:12]}",font=fnt(11),fill="#DCE6DD")
            meta={k:v for k,v in p.items() if k not in ("tags","query","recipe")}
            meta["candidate"]=chr(65+k)
            entry["candidates"].append(meta)
        if not photos:dr.text((338,y+75),"NO LICENSED EXACT CANDIDATE",font=fnt(16,True),fill="#E3A9A0")
        manifest.append(entry)
    name=OUT/f"PIP_Real_Photo_Candidates_Page_{page+1:02d}.jpg"
    board.save(name,quality=85,optimize=True)
    print("SAVED",name,os.path.getsize(name),flush=True)
(OUT/"PIP_Real_Photo_Candidates.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("TOTAL recipes with candidates",sum(bool(x["candidates"]) for x in manifest),"OF",len(manifest),flush=True)
