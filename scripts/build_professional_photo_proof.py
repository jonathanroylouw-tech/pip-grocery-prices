#!/usr/bin/env python3
from PIL import Image,ImageDraw,ImageFont,ImageOps
import requests,io,os,json
from pathlib import Path
PICKS=[[1,"Homemade burgers & chips",6006600],[2,"Steak & roast potatoes",7491903],[3,"Chicken breasts & mushrooms",31233887],[4,"Chicken schnitzel & potatoes",12502156],[7,"Chicken wraps",29535635],[8,"Sausages & onion gravy",10289307],[9,"Fish & chips",5863643],[14,"Chicken drumsticks & wedges",4589139],[15,"Spaghetti bolognese",116738],[21,"Beef tacos",5458335],[36,"Chicken noodle soup",10172749],[46,"Shakshuka & toast",6275109],[64,"Mushroom risotto",17800213]]
out=Path('previews/curated');out.mkdir(parents=True,exist_ok=True)
w,h=360,270;cols=4;rows=(len(PICKS)+cols-1)//cols
board=Image.new('RGB',(cols*w,rows*h+65),'#101715')
d=ImageDraw.Draw(board)
try: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
except: f=ImageFont.load_default()
try: fb=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',24)
except: fb=f
d.text((22,14),'PIP — PROFESSIONAL FOOD PHOTOGRAPHY SHORTLIST',fill='white',font=fb)
sources=[]
for k,(no,title,photo_id) in enumerate(PICKS):
    r,c=divmod(k,cols);x=c*w;y=r*h+65
    url=f'https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=1000'
    try:
        resp=requests.get(url,timeout=20)
        resp.raise_for_status()
        im=Image.open(io.BytesIO(resp.content)).convert('RGB')
        if im.width<400 or im.height<300:raise ValueError('too small')
        crop=ImageOps.fit(im,(w-8,h-68),Image.Resampling.LANCZOS)
        board.paste(crop,(x+4,y+4))
        good=True
    except Exception as e:
        d.rectangle((x+4,y+4,x+w-4,y+h-64),fill='#493b34')
        d.text((x+15,y+55),'IMAGE FETCH FAILED',fill='white',font=f)
        good=False
        print('ERROR',no,photo_id,e,flush=True)
    d.text((x+12,y+h-51),f'{no:02d}  {title[:32]}',fill='#FAFAF7',font=f)
    sources.append({'no':no,'recipe':title,'photo_id':photo_id,'photo_page':f'https://www.pexels.com/photo/{photo_id}/','license':'Pexels License','retrieved':good})
board.save(out/'PIP_Professional_Real_Photo_Picks_13.jpg',quality=89,optimize=True)
(out/'PIP_Pexels_Photo_Picks.json').write_text(json.dumps(sources,indent=2))
print('PASS',sum(p['retrieved'] for p in sources),'of',len(sources),'real photos ready',flush=True)
