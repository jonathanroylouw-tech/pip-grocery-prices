import requests,re,json
from bs4 import BeautifulSoup
samples={
'pexels':'https://www.pexels.com/search/beef%20tacos/',
'unsplash':'https://unsplash.com/s/photos/beef-tacos',
'openverse':'https://api.openverse.org/v1/images/?q=beef%20tacos&page_size=3',
'commons':'https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=beef%20tacos&gsrnamespace=6&gsrlimit=3&prop=imageinfo&iiprop=url%7Csize&format=json',
'pixabay':'https://pixabay.com/images/search/beef%20tacos/',
'themealdb':'https://www.themealdb.com/api/json/v1/1/search.php?s=tacos'
}
for label,u in samples.items():
 try:
  r=requests.get(u,headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36'},timeout=12)
  t=r.text
  imgs=re.findall(r'https?[^\" ]+?(?:jpg|jpeg|webp)(?:\?[^\" ]*)?',t,re.I)
  print(json.dumps(dict(label=label,status=r.status_code,size=len(r.content),url=r.url,images=imgs[:2],head=t[:90]),ensure_ascii=False),flush=True)
 except Exception as e:print(label,'ERROR',str(e),flush=True)

additional={
'pexels_direct':'https://images.pexels.com/photos/7613554/pexels-photo-7613554.jpeg?auto=compress&cs=tinysrgb&w=640',
'google_pexels':'https://www.google.com/search?q=site%3Apexels.com%2Fphoto%2F+chicken+wrap+food+photo',
'google_south_african':'https://www.google.com/search?q=site%3Apexels.com%2Fphoto%2F+bobotie+south+african+food',
'bing_pexels':'https://www.bing.com/search?q=site%3Apexels.com%2Fphoto%2F+chicken+curry+rice',
'rawpixel':'https://www.rawpixel.com/search/real%20chicken%20curry%20food%20photograph'
}
for label,u in additional.items():
 try:
  r=requests.get(u,headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36'},timeout=12)
  pics=re.findall(r'(?:https?://)?(?:www\\.)?pexels\\.com/photo/[^\\\\\"<> ]+',r.text)[:4]
  print(json.dumps({'label':label,'status':r.status_code,'bytes':len(r.content),'type':r.headers.get('Content-Type'),'pexels_links':pics,'text':r.text[:80] if 'text' in r.headers.get('Content-Type','') else ''}),flush=True)
 except Exception as e:print(label,'ERROR',str(e),flush=True)

for label in ('google_pexels','bing_pexels'):
 try:
  u=additional[label]; t=requests.get(u,timeout=9,headers={'User-Agent':'Mozilla/5.0'}).text
  ix=[m.start() for m in re.finditer('pexels',t,re.I)][:6]
  print('SNIPPET',label,'hits',len(ix),[t[max(0,i-100):i+200] for i in ix],flush=True)
 except Exception as e:print('SNIPERR',str(e))

for q in ['site:pexels.com/photo/ chicken curry rice','site:pexels.com/photo/ beef tacos','site:pexels.com/photo/ boerewors mash']:
 try:
  r=requests.get('https://www.bing.com/search',params={'q':q,'format':'rss'},timeout=14,headers={'User-Agent':'Mozilla/5.0'})
  links=re.findall(r'<link>(.*?)</link>',r.text)
  print('RSS',q,r.status_code,len(r.content),links[:7],flush=True)
 except Exception as e:print('RSS_ERROR',q,str(e),flush=True)
