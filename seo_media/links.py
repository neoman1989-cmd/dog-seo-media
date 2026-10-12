"""Official fallback; affiliate activation requires a matching owner-reviewed record."""
from datetime import date, datetime
from zoneinfo import ZoneInfo
from hashlib import sha256
import json
from urllib.parse import urlsplit

def secure(url):
    p=urlsplit(url)
    return p.scheme=='https' and bool(p.hostname) and not p.username and not p.password and p.port in (None,443)

def approval_digest(record):
    return sha256(json.dumps({k:v for k,v in record.items() if k!='owner_approval_hash'},ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def resolve(product,policy=None,today=None):
    official=product['source_url']
    if not secure(official): raise ValueError('Unsafe official URL')
    policy=policy or {'affiliate_enabled':False}
    record=product.get('affiliate',{})
    fallback={'url':official,'type':'official','rel':'noopener','reason':'affiliate_not_activated'}
    if policy.get('affiliate_enabled') is not True: return fallback
    try:
        if record['status']!='approved' or record['product_id']!=product['id']: return fallback
        if not all(isinstance(record.get(k),str) and record[k].strip() for k in ('asp','approval_id','owner_reviewer')): return fallback
        today=today or datetime.now(ZoneInfo('Asia/Tokyo')).date()
        if not date.fromisoformat(record['approved_on'])<=today<=date.fromisoformat(record['expires_on']): return fallback
        url=record['url']
        if not secure(url) or urlsplit(url).hostname not in policy['allowed_affiliate_hosts']: return fallback
        if record['owner_approval_hash']!=approval_digest(record): return fallback
    except (KeyError,TypeError,ValueError):return fallback
    return {'url':url,'type':'affiliate','rel':'sponsored nofollow noopener','reason':'owner_and_asp_approved'}
