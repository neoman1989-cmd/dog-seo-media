"""Offline Search Console export adapter. No credentials or network access."""
import csv
from decimal import Decimal
from urllib.parse import urlsplit


def import_search_console(path,site_host):
    rows=[]
    with open(path,newline='',encoding='utf-8-sig') as stream:
        reader=csv.DictReader(stream)
        required={'page','clicks','impressions','position'}
        if not required.issubset(reader.fieldnames or []): raise ValueError('Required normalized CSV columns are missing')
        for row in reader:
            url=urlsplit(row['page'])
            if url.scheme!='https' or url.hostname!=site_host or url.username or url.password or url.query:
                raise ValueError('Unexpected site or query parameters; avoid personal information')
            clicks,impressions=int(row['clicks']),int(row['impressions'])
            position=Decimal(row['position'])
            if not 0<=clicks<=impressions or not position.is_finite() or position<0: raise ValueError('Invalid metrics')
            rows.append({'page':row['page'],'clicks':clicks,'impressions':impressions,'ctr':str(Decimal(clicks)/impressions) if impressions else None,'position':str(position),'source':'user_export','automation':'review_only'})
    return rows
