"""Weekly offline analytics. Recommendations only, no uploads or publication."""
import argparse
import json
from pathlib import Path
from decimal import Decimal
from .analytics import import_search_console

def unique(rows):
    result={}
    for row in rows:
        if row['page'] in result:raise ValueError('Provide one aggregated row per page/week')
        result[row['page']]=row
    return result

def report(current,previous,data_label='owner_export'):
    now,before=unique(current),unique(previous)
    output=[]
    for url,row in now.items():
        old=before.get(url)
        sufficient=row['impressions']>=100
        action='manual_intent_and_internal_link_review' if sufficient and 8<=Decimal(row['position'])<=20 else ('insufficient_data' if not sufficient else 'monitor')
        output.append({**row,'click_delta':row['clicks']-old['clicks'] if old else None,'ctr_delta':str(Decimal(row['ctr'])-Decimal(old['ctr'])) if old and old['ctr'] is not None and row['ctr'] is not None else None,'action':action})
    return {'data_label':data_label,'pages':output,'automatic_rewrite':False,'automatic_publication':False,'scope_note':'Search Console averaged positions are not fixed rankings. Actions are editorial hypotheses.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--mock',action='store_true');p.add_argument('--current');p.add_argument('--previous');p.add_argument('--site-host');p.add_argument('--output',default='output/weekly.json');a=p.parse_args()
    if a.mock:
        current=[{'page':'https://example.invalid/camera/','clicks':12,'impressions':300,'ctr':'0.04','position':'12','source':'synthetic_fixture'}]
        previous=[{'page':'https://example.invalid/camera/','clicks':8,'impressions':200,'ctr':'0.04','position':'15','source':'synthetic_fixture'}]
        result=report(current,previous,'synthetic_fixture_not_site_performance')
    else:
        if not all((a.current,a.previous,a.site_host)):p.error('current, previous and site-host required')
        result=report(import_search_console(a.current,a.site_host),import_search_console(a.previous,a.site_host))
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
