"""Capture public documents with TLS verification; never log in or infer terms."""
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import urllib.request
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from .research import Text,normalize
HOSTS={'www.a8.net','media.a8.net','af.moshimo.com','www.valuecommerce.ne.jp','affiliate.amazon.co.jp','affiliate.rakuten.co.jp','www.ankerjapan.com','furbo.com','www.furbo.com','rs.sakura.ad.jp','www.xserver.ne.jp','www.conoha.jp','www.onamae.com'}
class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if urlsplit(newurl).scheme!='https' or urlsplit(newurl).hostname not in HOSTS:raise ValueError('Unapproved redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def capture(name,url):
    if urlsplit(url).scheme!='https' or urlsplit(url).hostname not in HOSTS:raise ValueError('Unapproved public source')
    record={'url':url,'checked_at':datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),'status':'unavailable'}
    try:
        with urllib.request.build_opener(Redirect).open(url,timeout=25) as r:
            raw=r.read(2_000_001)
            if len(raw)>2_000_000:raise ValueError('Document too large')
            encoding=r.headers.get_content_charset() or 'utf-8'
            try:decoded=raw.decode(encoding)
            except UnicodeDecodeError:
                decoded=raw.decode(encoding,errors='replace');record['decoding_warning']='Replacement characters: do not verify affected text'
            parser=Text();parser.feed(decoded);text=normalize(' '.join(parser.parts));file=Path('data/phase4')/(name+'.txt');file.write_text(text)
            record.update(status='captured',final_url=r.url,text_file=str(file),sha256=sha256(text.encode()).hexdigest(),raw_sha256=sha256(raw).hexdigest())
    except (OSError,ValueError) as exc:record['error']=str(exc)
    Path('data/phase4',name+'.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));return record
if __name__=='__main__':
    for name,url in json.loads(Path('data/phase4/public-sources.json').read_text()).items():print(name,capture(name,url)['status'])
