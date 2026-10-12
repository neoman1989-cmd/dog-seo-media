"""Read-only public research. No login, signup, paid API or tracking-link visits."""
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlsplit
import urllib.request
from zoneinfo import ZoneInfo
from .research import Text,normalize
HOSTS={'furbo.com','www.furbo.com','www.a8.net','www.fpc-pet.co.jp','www.notion.com','www.notion.so','www.shopify.com','www.freee.co.jp','go.chatwork.com','www.chatwork.com','www.xserver.ne.jp','www.conoha.jp','rakkoid.com','www.rakkoid.com'}
def safe(url):
    p=urlsplit(url)
    return p.scheme=='https' and p.hostname in HOSTS and not p.username and not p.password and p.port in (None,443)
class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not safe(newurl):raise ValueError('Unapproved redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def acquire(id,url,directory=Path('data/phase5/sources')):
    if not safe(url) or not id.replace('-','').isalnum():raise ValueError('Unapproved source')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    record={'id':id,'requested_url':url,'checked_at':datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),'status':'unavailable'}
    try:
        with urllib.request.build_opener(Redirect).open(url,timeout=25) as response:
            raw=response.read(2_000_001)
            if len(raw)>2_000_000:raise ValueError('Document too large')
            encoding=response.headers.get_content_charset() or 'utf-8'
            try:decoded=raw.decode(encoding)
            except UnicodeDecodeError:
                decoded=raw.decode(encoding,errors='replace');record['decoding_warning']='Ignore/reject any replacement-character quote'
            parser=Text();parser.feed(decoded);text=normalize(' '.join(parser.parts))
            (directory/(id+'.txt')).write_text(text)
            record.update(status='captured_not_reviewed',final_url=response.url,sha256=sha256(text.encode()).hexdigest(),raw_sha256=sha256(raw).hexdigest())
    except (OSError,ValueError) as exc:record['error']=str(exc)
    (directory/(id+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2));return record
if __name__=='__main__':
    for id,url in json.loads(Path('data/phase5/public-sources.json').read_text()).items():print(id,acquire(id,url)['status'])
