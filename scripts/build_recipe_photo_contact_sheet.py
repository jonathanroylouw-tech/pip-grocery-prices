#!/usr/bin/env python3
"""Create an offline, single-image contact sheet using real photographs (no AI).
Photos are reference candidates; no photo is represented as a guaranteed photo of
PIP's recipe. See generated JSON for source and licence evidence.
"""
import concurrent.futures, difflib, io, json, os, re, time, threading
from pathlib import Path
from urllib.parse import quote
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError
NAMES = ["Homemade burgers & chips","Steak & roast potatoes","Chicken breasts & mushrooms","Chicken schnitzel & potatoes","Boerewors & mash","Frikkadels & potatoes","Chicken wraps","Sausages & onion gravy","Fish & chips","Eggs, potatoes & spinach","Homemade chicken pizza","Tuna mayo jacket potatoes","Omelette & toast","Chicken drumsticks & wedges","Spaghetti bolognese","Creamy chicken mushroom pasta","Cottage pie","Mild chicken curry & rice","Tuna pasta bake","Chicken pesto-style pasta","Beef tacos","Chicken & vegetable traybake","Beef mince & potato skillet","Cheesy vegetable pasta bake","Beef bobotie","Chicken stew & pap","Boerewors, pap & chakalaka","Cape Malay chicken curry","Frikkadels in tomato sauce","Tomato bredie","Samp & beans","Easy bean bunny chow","Roasted butternut soup","Tomato & red lentil soup","Hearty beef vegetable soup","Chicken noodle soup","Creamy chicken & mushroom soup","Vegetable barley soup","Split pea & vegetable soup","Minestrone with beans","Chickpea & butternut curry","Spinach feta frittata","Lentil cottage pie","Bean chilli with rice","Roasted vegetable couscous","Shakshuka & toast","Moroccan beef lentil stew","Beef koftas with couscous","Lemon-herb hake & greens","Mild Thai-style vegetable curry","Butter chicken","Chicken biryani","Chana masala","Red lentil dal","Lamb rogan josh-style curry","Paneer and spinach curry","Japanese-style chicken curry","Vegetable fried rice","Ginger chicken noodle bowls","Korean-inspired beef rice bowls","Thai-style chicken coconut soup","Thai green-style chicken curry","Vietnamese-inspired beef noodle salad","Mushroom risotto","Spinach ricotta cannelloni","Classic lasagne","Gnocchi with roasted tomato sauce","Spanish chicken and chickpea stew","Greek lemon chicken and potatoes","Beef moussaka","Moroccan chickpea tagine","Shawarma-inspired chicken wraps","Mexican chicken enchiladas","Black bean chilli and baked sweet potatoes","French onion soup","Broccoli and cheddar soup","Chicken and sweetcorn chowder","Roast vegetable and red lentil soup","Slow-cooked beef potjie-style stew","Cape Malay-style lentil bobotie","Pap with tomato and bean relish","Warm chicken and roast vegetable salad"]
SEARCH = ["beef hamburger french fries","steak roasted potatoes","chicken breast mushroom sauce","chicken schnitzel potatoes","boerewors sausage mashed potatoes","South African frikkadels meatballs","chicken wrap","sausage onions gravy","fish and chips","spinach potato egg skillet","chicken pizza","tuna baked potato","omelette toast","chicken drumsticks roasted potato wedges","spaghetti bolognese","chicken mushroom pasta","cottage pie","chicken curry rice","tuna pasta bake","chicken pesto pasta","ground beef tacos","roasted chicken vegetables traybake","minced beef potatoes skillet","vegetable cheesy pasta bake","South African bobotie","chicken stew maize pap","boerewors pap chakalaka","Cape Malay chicken curry","meatballs tomato sauce","tomato bredie beef","samp beans South Africa","bean bunny chow","butternut squash soup","tomato lentil soup","beef vegetable soup","chicken noodle soup","chicken mushroom soup","vegetable barley soup","split pea soup","minestrone bean soup","chickpea butternut curry","spinach feta frittata","lentil shepherds pie","bean chilli rice","roasted vegetables couscous","shakshuka","Moroccan beef lentil stew","beef kofta couscous","hake fish grilled lemon","vegetable coconut curry","butter chicken Indian","chicken biryani","chana masala","red lentil dal","lamb rogan josh","palak paneer spinach","Japanese chicken curry","vegetable fried rice","chicken noodle stir fry","Korean beef rice bowl","Thai coconut chicken soup","Thai green chicken curry","Vietnamese beef noodle salad","mushroom risotto","spinach ricotta cannelloni","beef lasagna","gnocchi tomato sauce","Spanish chicken chickpea stew","Greek lemon roasted chicken potato","beef moussaka","Moroccan chickpea tagine","chicken shawarma wrap","chicken enchiladas","black bean chili sweet potato","French onion soup","broccoli cheddar soup","chicken corn chowder","roasted vegetables lentil soup","beef potjie stew","lentil bobotie","pap tomato relish beans","chicken roasted vegetables salad"]
OUT = Path("previews")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://raw.githubusercontent.com/ronaldl29/public-domain-recipes/main/static/pix/"
API = "https://api.github.com/repos/ronaldl29/public-domain-recipes/contents/static/pix"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "PIP-recipe-photo-contact/1.0"
try:
    listing = requests.get(API,timeout=20).json()
    FALLBACKS = [x["name"] for x in listing if x.get("name","").endswith(".webp") and x.get("size",0)<250000]
except Exception:
    FALLBACKS = []
print("Public-domain fallback image files:", len(FALLBACKS),flush=True)
photo_cache = {}
lock = threading.Lock()
def fetchimg(url, timeout=9):
    try:
        r = requests.get(url,timeout=timeout,headers={"User-Agent":"PIPPhotoBoard/1.0 (recipe photo research)"})
        if r.status_code != 200 or len(r.content)<3000 or len(r.content)>4_000_000: return None
        im=Image.open(io.BytesIO(r.content)); im.load()
        if im.width<170 or im.height<120: return None
        return im.convert("RGB")
    except Exception: return None


# No generic 'nearest dish' substitutions: verify prominent dish terms in source metadata.
def keywords(query):
    ignored={"and","with","style","inspired","mild","classic","homemade","easy","hearty","fresh","roasted","warm","the","rice","potato","potatoes","vegetable","vegetables","chicken","beef","sauce","soup","pasta"}
    return [w for w in re.findall(r"[a-z]+",query.lower()) if len(w)>=3 and w not in ignored]

def strict_score(title,query,photo=None):
    title=re.sub("<[^>]+>"," ",title.lower())
    qwords=keywords(query)
    matches=sum(1 for w in qwords if w in title)
    meal_words=["biryani","tacos","shakshuka","lasagna","lasagne","schnitzel","couscous","enchilada","omelette","bobotie","moussaka","risotto","cannelloni","chowder","gnocchi","kofta","curry","burger","stew","pizza","dal","pasta","wrap","fries","meatball","lentil","chili","chilli","frittata","soup","noodle"]
    if any(w in query.lower() for w in meal_words):
        core=[w for w in meal_words if w in query.lower()]
        if not any(w in title for w in core):return -999
    if matches < (1 if len(qwords)<3 else 2):return -999
    bad=["illustration","ai generated","generative","vector","painting","artwork","clipart","packaging","food package","menu board","recipe book","stock image"]
    if any(w in title for w in bad):return -999
    size_bonus=0
    if photo:
        width=photo.get("width") or 0; height=photo.get("height") or 0
        if width and height:
            if min(width,height)<350:return -999
            size_bonus=min(3,(width*height)/500000)
    return matches*5 + size_bonus

def commons_candidates(query):
    api="https://commons.wikimedia.org/w/api.php"
    try:
        params={"action":"query","format":"json","generator":"search",
          "gsrsearch":query+" filetype:bitmap","gsrnamespace":6,"gsrlimit":15,
          "prop":"imageinfo","iiprop":"url|size|extmetadata","iiurlwidth":640}
        res=requests.get(api,params=params,timeout=16,headers={"User-Agent":"PIPPhotoReview/1.0 (recipe contact sheet)"})
        if not res.ok:return []
        pages=res.json().get("query",{}).get("pages",{})
        results=[]
        for p in pages.values():
            info=(p.get("imageinfo") or [{}])[0]
            m=info.get("extmetadata") or {}
            license_name=(m.get("LicenseShortName") or {}).get("value","")
            lc=license_name.lower().replace(" ","")
            if not any(x in lc for x in ("cc-by","cc0","publicdomain")):continue
            photo={"url":info.get("thumburl") or info.get("url"),"source":"Wikimedia Commons",
             "photo_page":info.get("descriptionurl") or "","photographer":re.sub("<[^>]+>"," ",(m.get("Artist") or {}).get("value",""))[:180],
             "license":license_name,"width":info.get("width"),"height":info.get("height")}
            photo["title"]=p.get("title","").replace("File:","").replace("_"," ")
            results.append(photo)
        return results
    except Exception:return []

def openverse_candidates(query):
    try:
        resp=requests.get("https://api.openverse.org/v1/images/",params={"q":query,"page_size":20,"license":"cc0,pdm,by,by-sa"},timeout=16)
        if not resp.ok:return []
        out=[]
        for p in resp.json().get("results",[]):
            if (p.get("license") or "").lower() not in ("cc0","pdm","by","by-sa"):continue
            title=p.get("title") or ""
            tags=" ".join(x.get("name","") for x in (p.get("tags") or []) if isinstance(x,dict))
            out.append({"url":p.get("thumbnail") or p.get("url"),"source":"Openverse / "+str(p.get("source","")),
            "photo_page":p.get("foreign_landing_url") or "","photographer":p.get("creator") or "",
            "license":p.get("license"),"width":p.get("width"),"height":p.get("height"),"title":title,
            "tags":tags})
        return out
    except Exception:return []

def source_photo(name,query,idx):
    # Exact named dish, then short dish query, NEVER an unrelated fallback photograph.
    terms=[query,name]
    scored=[]
    for q in terms:
        for p in commons_candidates(q)+openverse_candidates(q):
            title=p.get("title","")+" "+p.get("tags","")
            score=strict_score(title,query,p)
            if score<0:continue
            # Prefer naturally shot, high-resolution photographs; no claims of guaranteed aesthetic quality.
            if "flickr" in p.get("source","").lower():score+=0.4
            scored.append((score,p))
        if scored:break
    scored.sort(key=lambda item:-item[0])
    seen=set()
    for score,p in scored[:14]:
        url=p.get("url") or ""
        page=p.get("photo_page") or url
        if not url or page in seen:continue
        seen.add(page)
        im=fetchimg(url,timeout=12)
        if im:
            return im,{"recipe":name,"source":p.get("source"),"photo_page":page,
             "photographer":p.get("photographer"),"license":p.get("license"),
             "match":"dish-keyword-matched candidate; aesthetic and ingredients still require visual approval",
             "score":round(score,2),"source_title":p.get("title","")}
    return None,{"recipe":name,"source":"none","match":"no suitably named licensed dish photograph found — not substituted"}

def font(size,bold=False):
    candidates=["/usr/share/fonts/truetype/dejavu/DejaVuSans-"+("Bold" if bold else "")+".ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for f in candidates:
        if os.path.exists(f):
            try:return ImageFont.truetype(f,size)
            except:pass
    return ImageFont.load_default()

def wrap(draw,s,ft,max_w):
    ws=s.split(" "); lines=[]; cur=""
    for w in ws:
        new=cur+" "+w if cur else w
        if draw.textbbox((0,0),new,font=ft)[2] > max_w and cur: lines.append(cur);cur=w
        else:cur=new
    if cur:lines.append(cur)
    return lines[:3]

cw,ch=300,260
cols=6; rows=(len(NAMES)+cols-1)//cols
board=Image.new("RGB",(cw*cols+60,rows*ch+205),(14,20,19))
draw=ImageDraw.Draw(board)
draw.text((36,32),"PIP  /  REAL FOOD PHOTO REFERENCES",font=font(35,True),fill=(249,249,244))
draw.text((38,85),"82 recipes  •  Actual photographs  •  Contact sheet for visual approval",font=font(19),fill=(182,194,183))
draw.text((38,117),"Some images are illustrative references, not exact photos of the named recipe.",font=font(15),fill=(205,182,141))
manifest=[]
def worker(arg):
    i,(name,query)=arg
    im,meta=source_photo(name,query,i)
    return i,im,meta
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    futs={pool.submit(worker,(i,(name,q))):i for i,(name,q) in enumerate(zip(NAMES,SEARCH))}
    for fut in concurrent.futures.as_completed(futs):
        i=futs[fut]
        try: i,im,meta=fut.result()
        except Exception as e: im=None; meta={"recipe":NAMES[i],"error":str(e),"match":"not sourced"}
        x=30+(i%cols)*cw; y=175+(i//cols)*ch
        draw.rounded_rectangle((x,y,x+cw-11,y+ch-12),radius=12,fill=(38,45,40))
        if im is not None:
            pic=ImageOps.fit(im,(cw-13,177),method=Image.Resampling.LANCZOS,centering=(0.5,0.48))
            board.paste(pic,(x+1,y+1))
        else:
            draw.text((x+16,y+64),"NEEDS CURATION",font=font(16,True),fill=(214,194,170))
        draw.text((x+13,y+184),"RECIPE "+str(i+1).zfill(2),font=font(12,True),fill=(163,181,159))
        for j,line in enumerate(wrap(draw,NAMES[i],font(15,True),cw-36)[:2]):
            draw.text((x+13,y+205+j*20),line,font=font(15,True),fill=(247,246,242))
        meta["recipe_no"]=i+1; meta["sourced"]=im is not None
        manifest.append(meta)
        if len(manifest)%10==0:print("Images processed:",len(manifest),flush=True)
manifest.sort(key=lambda x:x["recipe_no"])
count=sum(x["sourced"] for x in manifest)
board.save(OUT/"PIP_82_Curated_Dish_Matched_Photo_Sheet.png",optimize=True)
preview=board.copy()
preview.thumbnail((1500,3200),resample=Image.Resampling.LANCZOS)
preview.save(OUT/"PIP_82_Curated_Dish_Matched_Photo_Sheet_Preview.jpg",quality=63,optimize=True,subsampling=2)
print("Saved optimized JPG preview", (OUT/"PIP_82_Real_Food_Photo_Contact_Sheet_Preview.jpg").stat().st_size,flush=True)
(OUT/"PIP_82_Curated_Photo_Sources.json").write_text(json.dumps({"sourced":count,"total":len(NAMES),"images":manifest},indent=2))
print(f"Saved PNG: {count}/82 genuine photographs",flush=True)
