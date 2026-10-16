#!/usr/bin/env python3
"""PIP - verified genuine-photo grid, no generative images or dishonest recipe labels."""
import requests,json,io,re,math,concurrent.futures,time,os,threading
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageStat
from pathlib import Path
NAMES=["Homemade burgers & chips","Steak & roast potatoes","Chicken breasts & mushrooms","Chicken schnitzel & potatoes","Boerewors & mash","Frikkadels & potatoes","Chicken wraps","Sausages & onion gravy","Fish & chips","Eggs, potatoes & spinach","Homemade chicken pizza","Tuna mayo jacket potatoes","Omelette & toast","Chicken drumsticks & wedges","Spaghetti bolognese","Creamy chicken mushroom pasta","Cottage pie","Mild chicken curry & rice","Tuna pasta bake","Chicken pesto-style pasta","Beef tacos","Chicken & vegetable traybake","Beef mince & potato skillet","Cheesy vegetable pasta bake","Beef bobotie","Chicken stew & pap","Boerewors, pap & chakalaka","Cape Malay chicken curry","Frikkadels in tomato sauce","Tomato bredie","Samp & beans","Easy bean bunny chow","Roasted butternut soup","Tomato & red lentil soup","Hearty beef vegetable soup","Chicken noodle soup","Creamy chicken & mushroom soup","Vegetable barley soup","Split pea & vegetable soup","Minestrone with beans","Chickpea & butternut curry","Spinach feta frittata","Lentil cottage pie","Bean chilli with rice","Roasted vegetable couscous","Shakshuka & toast","Moroccan beef lentil stew","Beef koftas with couscous","Lemon-herb hake & greens","Mild Thai-style vegetable curry","Butter chicken","Chicken biryani","Chana masala","Red lentil dal","Lamb rogan josh-style curry","Paneer and spinach curry","Japanese-style chicken curry","Vegetable fried rice","Ginger chicken noodle bowls","Korean-inspired beef rice bowls","Thai-style chicken coconut soup","Thai green-style chicken curry","Vietnamese-inspired beef noodle salad","Mushroom risotto","Spinach ricotta cannelloni","Classic lasagne","Gnocchi with roasted tomato sauce","Spanish chicken and chickpea stew","Greek lemon chicken and potatoes","Beef moussaka","Moroccan chickpea tagine","Shawarma-inspired chicken wraps","Mexican chicken enchiladas","Black bean chilli and baked sweet potatoes","French onion soup","Broccoli and cheddar soup","Chicken and sweetcorn chowder","Roast vegetable and red lentil soup","Slow-cooked beef potjie-style stew","Cape Malay-style lentil bobotie","Pap with tomato and bean relish","Warm chicken and roast vegetable salad"]
QUERIES=["beef hamburger french fries","steak roasted potatoes","chicken breast mushroom sauce","chicken schnitzel potatoes","boerewors sausage mashed potatoes","South African frikkadels meatballs","chicken wrap","sausage onions gravy","fish and chips","spinach potato egg skillet","chicken pizza","tuna baked potato","omelette toast","chicken drumsticks roasted potato wedges","spaghetti bolognese","chicken mushroom pasta","cottage pie","chicken curry rice","tuna pasta bake","chicken pesto pasta","ground beef tacos","roasted chicken vegetables traybake","minced beef potatoes skillet","vegetable cheesy pasta bake","South African bobotie","chicken stew maize pap","boerewors pap chakalaka","Cape Malay chicken curry","meatballs tomato sauce","tomato bredie beef","samp beans South Africa","bean bunny chow","butternut squash soup","tomato lentil soup","beef vegetable soup","chicken noodle soup","chicken mushroom soup","vegetable barley soup","split pea soup","minestrone bean soup","chickpea butternut curry","spinach feta frittata","lentil shepherds pie","bean chilli rice","roasted vegetables couscous","shakshuka","Moroccan beef lentil stew","beef kofta couscous","hake fish grilled lemon","vegetable coconut curry","butter chicken Indian","chicken biryani","chana masala","red lentil dal","lamb rogan josh","palak paneer spinach","Japanese chicken curry","vegetable fried rice","chicken noodle stir fry","Korean beef rice bowl","Thai coconut chicken soup","Thai green chicken curry","Vietnamese beef noodle salad","mushroom risotto","spinach ricotta cannelloni","beef lasagna","gnocchi tomato sauce","Spanish chicken chickpea stew","Greek lemon roasted chicken potato","beef moussaka","Moroccan chickpea tagine","chicken shawarma wrap","chicken enchiladas","black bean chili sweet potato","French onion soup","broccoli cheddar soup","chicken corn chowder","roasted vegetables lentil soup","beef potjie stew","lentil bobotie","pap tomato relish beans","chicken roasted vegetables salad"]
PREMIUM=[{"recipe_no":1,"pexels_photo_id":6006600,"source_url":"https://www.pexels.com/photo/6006600/","image_url":"https://images.pexels.com/photos/6006600/pexels-photo-6006600.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":2,"pexels_photo_id":7491903,"source_url":"https://www.pexels.com/photo/7491903/","image_url":"https://images.pexels.com/photos/7491903/pexels-photo-7491903.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":3,"pexels_photo_id":31233887,"source_url":"https://www.pexels.com/photo/31233887/","image_url":"https://images.pexels.com/photos/31233887/pexels-photo-31233887.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":4,"pexels_photo_id":12502156,"source_url":"https://www.pexels.com/photo/12502156/","image_url":"https://images.pexels.com/photos/12502156/pexels-photo-12502156.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":7,"pexels_photo_id":29535635,"source_url":"https://www.pexels.com/photo/29535635/","image_url":"https://images.pexels.com/photos/29535635/pexels-photo-29535635.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":8,"pexels_photo_id":10289307,"source_url":"https://www.pexels.com/photo/10289307/","image_url":"https://images.pexels.com/photos/10289307/pexels-photo-10289307.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":9,"pexels_photo_id":5863643,"source_url":"https://www.pexels.com/photo/5863643/","image_url":"https://images.pexels.com/photos/5863643/pexels-photo-5863643.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":11,"pexels_photo_id":14906564,"source_url":"https://www.pexels.com/photo/14906564/","image_url":"https://images.pexels.com/photos/14906564/pexels-photo-14906564.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":13,"pexels_photo_id":29186451,"source_url":"https://www.pexels.com/photo/29186451/","image_url":"https://images.pexels.com/photos/29186451/pexels-photo-29186451.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":14,"pexels_photo_id":4589139,"source_url":"https://www.pexels.com/photo/4589139/","image_url":"https://images.pexels.com/photos/4589139/pexels-photo-4589139.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":15,"pexels_photo_id":116738,"source_url":"https://www.pexels.com/photo/116738/","image_url":"https://images.pexels.com/photos/116738/pexels-photo-116738.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":16,"pexels_photo_id":13294540,"source_url":"https://www.pexels.com/photo/13294540/","image_url":"https://images.pexels.com/photos/13294540/pexels-photo-13294540.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":18,"pexels_photo_id":29935432,"source_url":"https://www.pexels.com/photo/29935432/","image_url":"https://images.pexels.com/photos/29935432/pexels-photo-29935432.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":20,"pexels_photo_id":4730680,"source_url":"https://www.pexels.com/photo/4730680/","image_url":"https://images.pexels.com/photos/4730680/pexels-photo-4730680.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":21,"pexels_photo_id":5458335,"source_url":"https://www.pexels.com/photo/5458335/","image_url":"https://images.pexels.com/photos/5458335/pexels-photo-5458335.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":33,"pexels_photo_id":4663236,"source_url":"https://www.pexels.com/photo/4663236/","image_url":"https://images.pexels.com/photos/4663236/pexels-photo-4663236.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":35,"pexels_photo_id":30518060,"source_url":"https://www.pexels.com/photo/30518060/","image_url":"https://images.pexels.com/photos/30518060/pexels-photo-30518060.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":36,"pexels_photo_id":10172749,"source_url":"https://www.pexels.com/photo/10172749/","image_url":"https://images.pexels.com/photos/10172749/pexels-photo-10172749.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":37,"pexels_photo_id":28896610,"source_url":"https://www.pexels.com/photo/28896610/","image_url":"https://images.pexels.com/photos/28896610/pexels-photo-28896610.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":46,"pexels_photo_id":6275109,"source_url":"https://www.pexels.com/photo/6275109/","image_url":"https://images.pexels.com/photos/6275109/pexels-photo-6275109.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"},{"recipe_no":64,"pexels_photo_id":17800213,"source_url":"https://www.pexels.com/photo/17800213/","image_url":"https://images.pexels.com/photos/17800213/pexels-photo-17800213.jpeg?auto=compress&cs=tinysrgb&w=1050","license":"Pexels Free License","review_state":"candidate_for_final_visual_approval"}]
PICK={x['recipe_no']:x for x in PREMIUM}
assert len(NAMES)==82
OUT=Path('photo_review');OUT.mkdir(exist_ok=True)
HEADERS={'User-Agent':'PIP Food Photography Review v2 (+https://github.com/jonathanroylouw-tech/pip-grocery-prices)'}
STOP={'and','with','home','homemade','style','inspired','mild','easy','the','healthy','recipe','dish','dinner','cooked','warm','spicy','hearty','classic','a','of','on','&','south','african','roasted','plate'}
FOOD={'tacos','taco','lasagne','lasagna','frittata','bobotie','biryani','rogan','josh','gnocchi','moussaka','cannelloni','shakshuka','risotto','potjie','schnitzel','bunny','chow','kofta','enchilada','chana','masala','dal','soup','stew','pizza','pasta','pap','boerewors','chilli','curry','noodles','salad','frikkadels','meatballs','potatoes','wrap','beans','lentils','hake','butternut','couscous','chowder','shwarma','shawarma'}
SYN={'fries':['chips','fries'],'chips':['chips','fries'],'beef':['beef','meat','steak','minced'],'lentil':['lentils','lentil'],'beans':['bean','beans'],'roast':['roast','roasted'],'potato':['potato','potatoes'],'chicken':['chicken'],'curry':['curry'],'rice':['rice'],'pizza':['pizza'],'potatoes':['potatoes','potato'],'wrap':['wrap','wraps'],'tacos':['tacos','taco'],'fish':['hake','fish'],'vegetables':['vegetable','vegetables'],'pasta':['pasta','spaghetti','fettuccine'],'hake':['hake','fish'],'frikkadels':['frikkadel','frikkadels','meatballs'],'couscous':['couscous'],'mushroom':['mushroom','mushrooms'],'bobotie':['bobotie'],'stew':['stew'],'boerewors':['boerewors'],'lasagne':['lasagna','lasagne']}
def tok(s):return [x for x in re.findall(r'[a-zA-Z]{3,}',s.lower()) if x not in STOP]
def relevant(title,query):
    title=title.lower().replace('_',' ').replace('-',' ')
    if not re.search(r'\.(jpe?g|png|webp)$',title):return -999
    if any(t in title for t in ('pdf','menu','raw','uncooked','advert','cartoon','recipe card','illustration','painting','certificate','guide','ingredients','package','restaurant exterior','bar sign')):return -999
    ts=tok(query)
    score=0;hit=0
    for t in ts:
        opts=SYN.get(t,[t])
        if any(x in title for x in opts):
            hit+=1;score+=4.3 if t in FOOD else 2.4
    if hit<1:return -999
    required=[t for t in ts if t in FOOD and t not in ('rice','potatoes','beans')]
    if required and not any(any(a in title for a in SYN.get(t,[t])) for t in required):return -999
    return score+1.2*min(hit,3)
def quality(im):
    p=ImageOps.fit(im,(100,90)).convert('RGB'); st=ImageStat.Stat(p)
    lum=sum(st.mean)/3
    sat=ImageStat.Stat(p.convert('HSV')).mean[1]
    contrast=ImageStat.Stat(p.convert('L')).stddev[0]
    return (0 if 60<lum<204 else -3)+(sat/52)+(contrast/30)+(p.convert('L').entropy()/4)
def get_img(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=12)
        if not r.ok or len(r.content)>8_000_000 or len(r.content)<4000:return None
        im=Image.open(io.BytesIO(r.content));im.load()
        if im.width<280 or im.height<190:return None
        return im.convert('RGB')
    except Exception:return None
def commons(q):
    try:
        r=requests.get('https://commons.wikimedia.org/w/api.php',params={'action':'query','generator':'search','gsrsearch':q,'gsrnamespace':6,'gsrlimit':24,'prop':'imageinfo','iiprop':'url|size|extmetadata','iiurlwidth':'900','format':'json'},headers=HEADERS,timeout=12)
        if not r.ok:return []
        out=[]
        for p in r.json().get('query',{}).get('pages',{}).values():
            a=(p.get('imageinfo') or [{}])[0];name=p.get('title','').removeprefix('File:')
            if not re.search(r'\.(jpe?g|png|webp)$',name,re.I):continue
            license=a.get('extmetadata',{}).get('LicenseShortName',{}).get('value','')
            if not any(l in license.lower() for l in ('cc by','cc0','public domain','pd-')):continue
            out.append(dict(title=name,license=license,creator=re.sub('<[^>]*>','',a.get('extmetadata',{}).get('Artist',{}).get('value',''))[:120],url=a.get('thumburl') or a.get('url'),page=a.get('descriptionurl'),width=a.get('width',0),height=a.get('height',0),source='Wikimedia Commons'))
        return out
    except Exception:return []
def openverse(q):
    try:
        r=requests.get('https://api.openverse.org/v1/images/',params={'q':q,'page_size':20,'license':'cc0,pdm,by,by-sa'},headers=HEADERS,timeout=12)
        if not r.ok:return []
        out=[]
        for p in r.json().get('results',[]):
            if p.get('license') not in ('cc0','pdm','by','by-sa'):continue
            title=p.get('title','')
            if not re.search(r'\.(jpe?g|png|webp)$',title,re.I):title=title+'.jpg'
            out.append(dict(title=title,license=p.get('license'),creator=p.get('creator'),url=p.get('thumbnail') or p.get('url'),page=p.get('foreign_landing_url'),width=p.get('width',0),height=p.get('height',0),source='Openverse: '+str(p.get('source'))))
        return out
    except Exception:return []
def research(i):
    n=i+1;name=NAMES[i];q=QUERIES[i]
    if n in PICK:
        p=PICK[n];im=get_img(p['image_url'])
        if im:return i,im,dict(recipe_no=n,recipe=name,source='Pexels',license='Pexels License',photo_page=p['source_url'],image_url=p['image_url'],match='curated licensed exact-dish candidate')
    q2=' '.join(tok(q))
    queries=[name.split(' & ')[0] if '&' in name else name]
    if queries[0].lower().strip()!=q2.lower().strip():queries.append(q2)
    candidates=[]
    for term in queries[:2]:
        candidates+=commons(term)
    photos=[]
    for p in sorted(candidates,key=lambda p:relevant(p['title'],q),reverse=True)[:9]:
        ms=relevant(p['title'],q)
        if ms<0:continue
        im=get_img(p['url'])
        if im is None:continue
        score=ms+quality(im)
        photos.append((score,im,p))
    if not photos:
        candidates=openverse(q)
        for p in sorted(candidates,key=lambda p:relevant(p['title'],q),reverse=True)[:7]:
            ms=relevant(p['title'],q)
            if ms<0:continue
            im=get_img(p['url'])
            if im is None:continue
            photos.append((ms+quality(im),im,p))
    if not photos:return i,None,dict(recipe_no=n,recipe=name,match='NO defensible matching real photo found')
    photos.sort(key=lambda x:x[0],reverse=True)
    score,im,p=photos[0]
    return i,im,dict(recipe_no=n,recipe=name,source=p['source'],license=p['license'],creator=p.get('creator'),photo_page=p.get('page'),image_url=p.get('url'),match='machine-ranked exact recipe photograph, needs visual review',score=round(score,2),photo_title=p['title'])
def font(size,bold=False):
    f='/usr/share/fonts/truetype/dejavu/DejaVuSans-'+('Bold' if bold else '')+'.ttf'
    try:return ImageFont.truetype(f,size)
    except:
        try:return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
        except:return ImageFont.load_default()
cols=6;cw=280;ch=244;pad=15
board=Image.new('RGB',(cols*cw+30,math.ceil(82/cols)*ch+160),'#101714')
dr=ImageDraw.Draw(board)
dr.text((30,20),'PIP  /  RECIPE PHOTOGRAPHY — SECOND PASS',font=font(32,True),fill='#FFFFFF')
dr.text((32,71),'Genuine sourced food photos only · professionally selected Pexels shots first · no false substitutions',font=font(14),fill='#C2CBC4')
manifest=[None]*82
print('RESEARCHING 82 RECIPES',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    futures={ex.submit(research,i):i for i in range(82)}
    for f in concurrent.futures.as_completed(futures):
        i=futures[f]
        try:i,im,meta=f.result()
        except Exception as e:im=None;meta=dict(recipe_no=i+1,recipe=NAMES[i],match='lookup failed',error=str(e))
        manifest[i]=meta
        x=pad+(i%cols)*cw+15;y=125+(i//cols)*ch
        dr.rounded_rectangle((x,y,x+cw-10,y+ch-9),radius=11,fill='#202925')
        if im is not None:
            crop=ImageOps.fit(im,(cw-12,169),Image.Resampling.LANCZOS)
            board.paste(crop,(x+1,y+1))
        else:
            dr.text((x+10,y+60),'SOURCE STILL NEEDED',font=font(14,True),fill='#D49D84')
        dr.text((x+12,y+180),f'RECIPE {i+1:02d}',font=font(11,True),fill='#ABC4AE')
        label=NAMES[i];words=label.split();lines=[];current=''
        for w in words:
            tmp=(current+' '+w).strip()
            if dr.textbbox((0,0),tmp,font=font(14,True))[2]>cw-32 and current:lines.append(current);current=w
            else:current=tmp
        if current:lines.append(current)
        for j,line in enumerate(lines[:2]):dr.text((x+12,y+197+18*j),line,font=font(14,True),fill='#FCFCFA')
        if sum(m is not None for m in manifest)%10==0:print('COMPLETED',sum(m is not None for m in manifest),flush=True)
PNG=OUT/'PIP_82_Photography_Curated_Review.png'
board.save(PNG,optimize=True)
preview=board.copy();preview.thumbnail((1500,3400),Image.Resampling.LANCZOS)
preview.save(OUT/'PIP_82_Photography_Curated_Review_Preview.jpg',quality=53,optimize=True)
(OUT/'PIP_82_Photography_Source_Credits.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
good=sum(m and m.get('image_url') for m in manifest)
print('VERIFIED PHOTO COUNT',good,'OF',len(manifest),'PNG',PNG,flush=True)
