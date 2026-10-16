import requests,json,time,re
terms={27:['boerewors pap chakalaka','Pap with sheba, wors and mutton chop','Chakalaka meal'],28:['Cape Malay chicken curry','Cape Malay curry','Chicken curry cooked'],32:['bunny chow bean curry','bunny chow','Bunny Chow Durban'],47:['Moroccan beef lentil stew','Moroccan beef stew','Moroccan tagine with beef'],48:['beef kofta couscous','kofta kebab','Kofta with couscous'],49:['hake fish lemon greens','pan seared hake fish','grilled hake fillet'],69:['Greek lemon chicken potatoes','Greek chicken potatoes','lemon chicken potatoes'],79:['potjiekos','beef potjie','potjie stew'],81:['pap with sheba tomato relish','Putu pap and beans with chakalaka','pap tomato relish']}
for n,queries in terms.items():
 for term in queries:
  try:
   r=requests.get('https://commons.wikimedia.org/w/api.php',params={'action':'query','generator':'search','gsrsearch':term,'gsrnamespace':6,'gsrlimit':8,'prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':800,'format':'json'},timeout=10,headers={'User-Agent':'PIP research contact sheet'})
   a=[]
   for p in r.json().get('query',{}).get('pages',{}).values():
    ti=p['title']
    if not re.search(r'\.(jpe?g|png|webp)$',ti,re.I):continue
    item=p.get('imageinfo',[{}])[0]
    l=item.get('extmetadata',{}).get('LicenseShortName',{}).get('value','')
    if not any(x in l.lower() for x in ('cc by','cc0','public domain','pd-')):continue
    a.append({'title':ti,'url':item.get('thumburl') or item.get('url'),'page':item.get('descriptionurl'),'license':l})
   print('RESULT',n,term,json.dumps(a[:5]),flush=True)
  except Exception as e:print('ERR',n,term,str(e)[:100])
