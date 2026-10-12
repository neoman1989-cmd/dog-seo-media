"""Phase 5: only evidence-bound public fixed JPY rewards enter conditional models."""
from datetime import date,datetime
from decimal import Decimal, ROUND_CEILING
from hashlib import sha256
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from .monetization import estimate,number
PROVIDER_HOSTS={'www.xserver.ne.jp','www.conoha.jp','rakkoid.com'}

def validate_program(program,root=Path('.'),today=None):
    from urllib.parse import urlsplit
    today=today or datetime.now(ZoneInfo('Asia/Tokyo')).date()
    errors=[]
    if program.get('status')!='public_fixed_reward_outcome_verified': errors.append('reward_or_outcome_not_verified')
    reward=program.get('reward_jpy')
    if type(reward) is not int or reward<=0:errors.append('fixed_positive_jpy_reward_required')
    if program.get('currency')!='JPY':errors.append('currency_not_jpy')
    if program.get('inactive') is not False:errors.append('availability_unverified_or_closed')
    try:
        age=(today-date.fromisoformat(program['checked_on'])).days
        if not 0<=age<=30:errors.append('evidence_stale')
        base=Path(root).resolve()
        path=(base/program['source_file']).resolve()
        if not path.is_relative_to(base/'data/phase5/sources'):raise ValueError('Invalid evidence path')
        text=path.read_text();capture=json.loads(path.with_suffix('.json').read_text())
        url=urlsplit(program['source_url'])
        if url.scheme!='https' or url.hostname not in PROVIDER_HOSTS or url.username or url.password or url.port not in (None,443):errors.append('unapproved_source')
        if capture.get('status')!='captured_not_reviewed' or capture.get('final_url')!=program['source_url']:errors.append('capture_source_mismatch')
        if sha256(text.encode()).hexdigest()!=program['source_sha256']:errors.append('source_hash_mismatch')
        for key in ('existence_quote','reward_quote','outcome_quote'):
            quote=program[key]
            if not quote or quote not in text or '\ufffd' in quote:errors.append('missing_or_invalid_'+key)
        if type(reward) is int and not any(token in program['reward_quote'] for token in (f'{reward:,}円',f'{reward}円')):errors.append('reward_does_not_match_quote')
        binding={k:v for k,v in program.items() if k!='review_hash'}
        expected=sha256(json.dumps(binding,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        if program.get('review_hash')!=expected or not program.get('reviewer'):errors.append('review_missing_or_changed')
    except (KeyError,OSError,ValueError,TypeError):errors.append('evidence_missing_or_invalid')
    return errors

def model(program,assumptions,target=50000,root=Path('.'),today=None):
    errors=validate_program(program,root,today)
    if errors:return {'program_id':program.get('id'),'status':'excluded','reasons':errors,'required_pv':None,'actual_revenue_jpy':None}
    if 'reward_jpy' in assumptions:raise ValueError('Reward override forbidden; use verified program reward')
    scenario={**assumptions,'reward_jpy':program['reward_jpy']}
    result=estimate(scenario,target)
    result.update(program_id=program['id'],status='conditional_public_terms_model',reward_source=program['source_url'],partner_approved=program.get('partner_approved') is True,actual_revenue_jpy=None,warning='Public reward confirmed; personal eligibility, approval and traffic remain unverified. Not a forecast.')
    # approval_rate is already used by estimate; accepted conversions count excludes that rate.
    result['required_approved_outcomes']=int(((number(target)+number(scenario['monthly_cost_jpy']))/program['reward_jpy']).to_integral_value(rounding=ROUND_CEILING))
    return result

def build():
    programs=json.loads(Path('data/phase5/programs.json').read_text())
    assumptions=json.loads(Path('data/phase5/funnel-assumptions.json').read_text())
    rows=[]
    for p in programs:
        if validate_program(p):rows.append(model(p,assumptions[0]));continue
        for a in assumptions:
            for target in (50000,100000):rows.append(model(p,a,target))
    path=Path('artifacts/phase5/models.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':build()
