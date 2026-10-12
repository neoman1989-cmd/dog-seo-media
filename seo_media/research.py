"""Free official-page research. No prices inferred; no automatic fact approval."""
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request
import urllib.parse
from zoneinfo import ZoneInfo

ALLOWED_HOSTS = {'www.tp-link.com','www.tapo.com','www.furbo.com','furbo.com'}
class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.hidden=max(0,self.hidden-1)
    def handle_data(self,data):
        if not self.hidden: self.parts.append(data)

def normalize(value): return ' '.join(value.split())
def allowed(url):
    p=urllib.parse.urlsplit(url)
    return p.scheme=='https' and p.hostname in ALLOWED_HOSTS and not p.username and not p.password and p.port in (None,443)
class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not allowed(newurl): raise ValueError('Non-allowlisted redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def acquire(product,directory):
    url=product['source_url']
    if not allowed(url): raise ValueError('Official source not allowlisted')
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    attempt={'url':url,'checked_at':datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),'status':'unavailable'}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'DogMediaResearch/0.1 (manual editorial research)'})
        with urllib.request.build_opener(OfficialRedirect).open(req,timeout=20) as response:
            raw=response.read(2_000_001)
            if len(raw)>2_000_000: raise ValueError('Page too large')
            parser=Text(); parser.feed(raw.decode(response.headers.get_content_charset() or 'utf-8'))
            text=normalize(' '.join(parser.parts))
            if len(text)<100: raise ValueError('Insufficient source text')
            target=directory/(product['id']+'.txt'); target.write_text(text)
            attempt.update(status='captured_not_reviewed',final_url=response.url,text_file=target.as_posix(),sha256=sha256(text.encode()).hexdigest())
    except (OSError,ValueError) as exc:
        attempt['error']=str(exc)
    (directory/(product['id']+'.json')).write_text(json.dumps(attempt,ensure_ascii=False,indent=2))
    return attempt

if __name__=='__main__':
    products=json.loads(Path('data/research/products.json').read_text())
    for product in products:
        print(product['id'],acquire(product,'data/evidence')['status'])
