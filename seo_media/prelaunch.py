"""Read-only readiness checklist; no DNS, deployment, purchases or publication."""
import argparse,json
from pathlib import Path
from .monetization import number
FLAGS=('owner_launch_approved','owner_billing_approved','domain_and_host_quote_confirmed','staging_smoke_passed','backup_restore_tested','privacy_and_ad_policy_reviewed','sources_and_stock_rechecked','official_links_or_approved_ads_tested','search_console_ownership_confirmed','analytics_consent_tested','monetization_hypothesis_reviewed')
def check(config):
    missing=[flag for flag in FLAGS if config.get(flag) is not True]
    for field,cap in [('initial_cost_jpy',30000),('monthly_total_cost_jpy',3000)]:
        try:
            if number(config[field])>cap:missing.append(field+'_over_budget')
        except (KeyError,ValueError,ArithmeticError):missing.append(field+'_unknown')
    return {'ready_for_owner_review':not missing,'missing':missing,'publication_performed':False,'purchases_performed':False,'note':'Checklist metadata only; actual owner approval and evidence still required.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config');a=p.parse_args();result=check(json.loads(Path(a.config).read_text()));print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['ready_for_owner_review'] else 2)
