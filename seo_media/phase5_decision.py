"""Read-only 90-day gates; inadequate evidence never becomes a pivot approval."""
from .monetization import number

def assess(observation):
    try:
        if number(observation['initial_spend_jpy'])>30000 or number(observation['monthly_total_spend_jpy'])>3000:
            return {'decision':'stop_additional_spend','reason':'budget_exceeded','site_changes':False}
    except (KeyError,ValueError,ArithmeticError):return {'decision':'hold','reason':'cost_unknown','site_changes':False}
    if observation.get('owner_allows_live_validation') is not True:
        return {'decision':'offline_parallel_only','reason':'no_permission_for_accounts_or_publication','site_changes':False}
    if not all(observation.get(k) is True for k in ('personal_terms_verified','serp_reviewed','tracking_verified')):
        return {'decision':'hold','reason':'eligibility_or_search_or_tracking_unverified','site_changes':False}
    days=observation.get('observation_days',0);clicks=observation.get('tracked_outbound_clicks',0);outcomes=observation.get('approved_outcomes',0)
    if any(type(v) is not int or v<0 for v in (days,clicks,outcomes)):raise ValueError('Invalid measured data')
    if days<45 or clicks<300:return {'decision':'hold','reason':'insufficient_observation','site_changes':False}
    if outcomes==0:return {'decision':'review_offer_or_intent','reason':'zero_outcomes_with_sample_not_genre_failure_proof','site_changes':False}
    return {'decision':'continue_bounded_validation','reason':'some_approved_outcomes_reassess_observed_revenue_per_pv','site_changes':False}
