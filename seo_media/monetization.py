"""Hypothesis calculator. All results are scenarios, never revenue predictions."""
from decimal import Decimal, ROUND_CEILING
import json
from pathlib import Path

def number(value):
    n=Decimal(str(value))
    if not n.is_finite() or n<0: raise ValueError('Nonnegative finite value required')
    return n

def estimate(scenario,target=50000):
    pv=number(scenario['monthly_pv']); ctr=number(scenario['outbound_ctr']); cvr=number(scenario['conversion_rate']); approval=number(scenario['approval_rate']); reward=number(scenario['reward_jpy']); cost=number(scenario['monthly_cost_jpy'])
    if any(rate>1 for rate in (ctr,cvr,approval)):raise ValueError('Rates must be fractions between 0 and 1')
    if cost>3000:raise ValueError('Monthly operating budget exceeded')
    per_pv=ctr*cvr*approval*reward
    revenue=pv*per_pv
    required=((number(target)+cost)/per_pv).to_integral_value(rounding=ROUND_CEILING) if per_pv else None
    return {'assumptions':scenario,'revenue_jpy':str(revenue),'profit_jpy':str(revenue-cost),'required_pv_for_target':int(required) if required is not None else None,'target_profit_jpy':str(target),'evidence_status':'hypothesis_not_forecast','external_api_calls':0}

if __name__=='__main__':
    scenarios=json.loads(Path('data/phase4/scenarios.json').read_text())
    Path('artifacts/phase4/profitability.json').write_text(json.dumps([estimate(s,target) for s in scenarios for target in (50000,100000)],ensure_ascii=False,indent=2))
