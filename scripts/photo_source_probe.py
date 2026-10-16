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
