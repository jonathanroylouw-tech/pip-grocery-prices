#!/usr/bin/env python3
"""Regenerate PIP food-photography contact sheet with curated dish-specific fixes.
All photographic files are real sources, never generated images. Accuracy caveats are carried in the manifest.
"""
import json,io,math,re,time,os,concurrent.futures
from pathlib import Path
import requests
from PIL import Image,ImageDraw,ImageFont,ImageOps
NAMES = ["Homemade burgers & chips","Steak & roast potatoes","Chicken breasts & mushrooms","Chicken schnitzel & potatoes","Boerewors & mash","Frikkadels & potatoes","Chicken wraps","Sausages & onion gravy","Fish & chips","Eggs, potatoes & spinach","Homemade chicken pizza","Tuna mayo jacket potatoes","Omelette & toast","Chicken drumsticks & wedges","Spaghetti bolognese","Creamy chicken mushroom pasta","Cottage pie","Mild chicken curry & rice","Tuna pasta bake","Chicken pesto-style pasta","Beef tacos","Chicken & vegetable traybake","Beef mince & potato skillet","Cheesy vegetable pasta bake","Beef bobotie","Chicken stew & pap","Boerewors, pap & chakalaka","Cape Malay chicken curry","Frikkadels in tomato sauce","Tomato bredie","Samp & beans","Easy bean bunny chow","Roasted butternut soup","Tomato & red lentil soup","Hearty beef vegetable soup","Chicken noodle soup","Creamy chicken & mushroom soup","Vegetable barley soup","Split pea & vegetable soup","Minestrone with beans","Chickpea & butternut curry","Spinach feta frittata","Lentil cottage pie","Bean chilli with rice","Roasted vegetable couscous","Shakshuka & toast","Moroccan beef lentil stew","Beef koftas with couscous","Lemon-herb hake & greens","Mild Thai-style vegetable curry","Butter chicken","Chicken biryani","Chana masala","Red lentil dal","Lamb rogan josh-style curry","Paneer and spinach curry","Japanese-style chicken curry","Vegetable fried rice","Ginger chicken noodle bowls","Korean-inspired beef rice bowls","Thai-style chicken coconut soup","Thai green-style chicken curry","Vietnamese-inspired beef noodle salad","Mushroom risotto","Spinach ricotta cannelloni","Classic lasagne","Gnocchi with roasted tomato sauce","Spanish chicken and chickpea stew","Greek lemon chicken and potatoes","Beef moussaka","Moroccan chickpea tagine","Shawarma-inspired chicken wraps","Mexican chicken enchiladas","Black bean chilli and baked sweet potatoes","French onion soup","Broccoli and cheddar soup","Chicken and sweetcorn chowder","Roast vegetable and red lentil soup","Slow-cooked beef potjie-style stew","Cape Malay-style lentil bobotie","Pap with tomato and bean relish","Warm chicken and roast vegetable salad"]
OVERRIDES={"6":["pexels",17989471,"Frikkadels / cooked meatball reference; verify potato accompaniment"],"22":["pexels",10821324,"Roast chicken, potatoes and vegetables; suitable traybake"],"24":["pexels",38090650,"Cheesy baked macaroni and vegetables"],"27":["commons","Chakalaka meal.jpg","Chakalaka served with meat; pap/boerewors not guaranteed"],"28":["pexels",35158690,"Chicken curry photograph; Cape Malay spice profile not visually verifiable"],"32":["commons","Bunny Chow.jpg","Bunny chow; bean filling not guaranteed"],"34":["pexels",4669274,"Tomato and red lentil soup"],"35":["pexels",37065023,"Beef and vegetable stew; soup consistency may differ"],"47":["pexels",5531292,"Beef stew with vegetables; lentils not visibly confirmed"],"48":["pexels",26341210,"Kofta with rice; couscous accompaniment differs"],"49":["pexels",5741445,"Grilled fish with broccoli and lemon; fish species not confirmed as hake"],"51":["pexels",9609844,"Butter chicken"],"52":["pexels",33947401,"Chicken biryani"],"53":["pexels",9287035,"Chana masala"],"54":["pexels",20004800,"Indian lentil soup; dal presentation reference"],"56":["pexels",31249589,"Palak paneer"],"58":["pexels",35071826,"Vegetable fried rice"],"61":["pexels",35049889,"Tom Kha Gai Thai coconut chicken soup"],"63":["pexels",30136632,"Vietnamese beef noodle salad"],"69":["pexels",4589138,"Roast chicken with potatoes; lemon not visually confirmed"],"70":["pexels",29535638,"Baked eggplant moussaka"],"75":["pexels",29653176,"French onion soup with browned cheese"],"77":["pexels",29538427,"Chicken sweetcorn soup"],"78":["pexels",6120511,"Lentil and vegetable soup; roasted component not visually verifiable"],"79":["commons","Beef Potjie Kos.jpg","South African beef potjie"],"81":["commons","Putu pap and beans with chakalaka.JPG","Pap with beans and chakalaka (relish variation)"]}
OUT=Path('photo_review');OUT.mkdir(exist_ok=True)
OLD=json.loads((OUT/'PIP_82_Photography_Source_Credits.json').read_text())
assert len(OLD)==len(NAMES)==82
HDR={'User-Agent':'PIP Real Recipe Photography Review/3.0'}
def grab(url):
    if not url:return None
    try:
        r=requests.get(url,headers=HDR,timeout=13)
        if not r.ok or len(r.content)<4500 or len(r.content)>9_000_000:return None
        im=Image.open(io.BytesIO(r.content));im.load()
        if im.width<180 or im.height<160:return None
        return im.convert('RGB')
    except Exception:return None
def resolve_commons(file):
    try:
        r=requests.get('https://commons.wikimedia.org/w/api.php',params={'action':'query','titles':'File:'+file,'prop':'imageinfo','iiprop':'url|size|extmetadata','iiurlwidth':900,'format':'json'},headers=HDR,timeout=12)
        if not r.ok:return None
        d=list(r.json().get('query',{}).get('pages',{}).values())[0]
        x=(d.get('imageinfo') or [{}])[0]; license=x.get('extmetadata',{}).get('LicenseShortName',{}).get('value','')
        if not any(t in license.lower() for t in ('cc by','cc0','public domain','pd-')):return None
        return dict(url=x.get('thumburl') or x.get('url'),image_url=x.get('thumburl') or x.get('url'),photo_page=x.get('descriptionurl'),source='Wikimedia Commons',license=license,creator=re.sub('<[^>]*>','',x.get('extmetadata',{}).get('Artist',{}).get('value',''))[:120])
    except Exception:return None
def process(i):
    data=dict(OLD[i]); n=i+1; override=OVERRIDES.get(str(n))
    if override:
        typ,name,note=override
        if typ=='pexels':
            url=f'https://images.pexels.com/photos/{name}/pexels-photo-{name}.jpeg?auto=compress&cs=tinysrgb&w=980'
            d=dict(source='Pexels',license='Pexels License',photo_page=f'https://www.pexels.com/photo/{name}/',image_url=url,match='curated photo candidate, source checked',review_note=note)
        else:
            info=resolve_commons(name)
            if info is None:return i,None,dict(recipe_no=n,recipe=NAMES[i],match='Photo lookup failed',review_note=note)
            d=dict(info,match='open licensed image candidate',review_note=note)
        photo=grab(d['image_url'])
        if photo is not None:
            data.update(d)
            return i,photo,data
        print('OVERRIDE ERROR',n,typ,name,flush=True)
    if data.get('image_url'):
        im=grab(data['image_url'])
        if im:return i,im,data
    return i,None,data
def font(sz,b=False):
    for f in (('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf') if b else ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),):
        if os.path.exists(f):return ImageFont.truetype(f,sz)
    return ImageFont.load_default()
cols=6;cw=280;ch=238
board=Image.new('RGB',(cols*cw+30,math.ceil(82/cols)*ch+175),'#101714')
d=ImageDraw.Draw(board)
d.text((32,21),'PIP  /  82 REAL FOOD PHOTOGRAPHS',font=font(33,True),fill='#FFFFFF')
d.text((32,73),'V3 photographic contact sheet  ·  review exact dish match / presentation  ·  unapproved app assets',font=font(15),fill='#CDDBD0')
meta=[None]*82
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:
    futures={ex.submit(process,i):i for i in range(82)}
    for fu in concurrent.futures.as_completed(futures):
        i,im,data=fu.result()
        x=30+(i%cols)*cw;y=135+(i//cols)*ch
        meta[i]=data
        d.rounded_rectangle((x,y,x+cw-10,y+ch-10),radius=10,fill='#24302B')
        if im:
            crop=ImageOps.fit(im,(cw-12,166),Image.Resampling.LANCZOS)
            board.paste(crop,(x+1,y+1))
            data['image_downloaded']=True
        else:
            d.text((x+8,y+66),'IMAGE STILL NEEDED',font=font(14,True),fill='#D8A69E')
            data['image_downloaded']=False
        d.text((x+12,y+178),f'RECIPE {i+1:02d}',font=font(11,True),fill='#ADBAAF')
        label=NAMES[i];words=label.split();lines=[];cur=''
        for w in words:
            next=(cur+' '+w).strip()
            if d.textbbox((0,0),next,font=font(13,True))[2]>cw-38 and cur:lines.append(cur);cur=w
            else:cur=next
        if cur:lines.append(cur)
        for k,line in enumerate(lines[:2]):d.text((x+12,y+196+18*k),line,font=font(13,True),fill='#FFFFFF')
        if sum(v is not None for v in meta)%10==0:print('PLACED',sum(v is not None for v in meta),flush=True)
board.save(OUT/'PIP_82_Real_Food_Review_V3.png',optimize=True)
preview=board.copy();preview.thumbnail((1500,3300),Image.Resampling.LANCZOS)
preview.save(OUT/'PIP_82_Real_Food_Review_V3_Preview.jpg',quality=60,optimize=True)
(OUT/'PIP_82_Real_Food_Sources_V3.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
print('PHOTOGRAPHS',sum(bool(x['image_downloaded']) for x in meta),'OF',len(meta),flush=True)
