from datetime import date
from hashlib import sha256
import copy,json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from seo_media.opportunities import validate_program,model
from seo_media.phase5_decision import assess
from seo_media.phase5_research import acquire
class OpportunityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        source=self.root/'data/phase5/sources/fixture.txt';source.parent.mkdir(parents=True)
        text='案件の存在。成約報酬 スタンダード 5,000円 /件。広告経由のサービス成約。'
        source.write_text(text);source.with_suffix('.json').write_text(json.dumps({'status':'captured_not_reviewed','final_url':'https://www.xserver.ne.jp/affiliate.php'}))
        self.program={'id':'fixture-only','status':'public_fixed_reward_outcome_verified','reward_jpy':5000,'currency':'JPY','inactive':False,'checked_on':'2026-10-12','source_file':'data/phase5/sources/fixture.txt','source_url':'https://www.xserver.ne.jp/affiliate.php','source_sha256':sha256(text.encode()).hexdigest(),'existence_quote':'案件の存在','reward_quote':'スタンダード 5,000円 /件','outcome_quote':'広告経由のサービス成約','reviewer':'fixture','partner_approved':False}
        self.bind()
        self.assumptions={'monthly_pv':10000,'outbound_ctr':.08,'conversion_rate':.01,'approval_rate':.6,'monthly_cost_jpy':3000}
    def bind(self):self.program['review_hash']=sha256(json.dumps({k:v for k,v in self.program.items() if k!='review_hash'},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    def test_verified_reward_only(self):
        result=model(self.program,self.assumptions,root=self.root,today=date(2026,10,12))
        self.assertEqual(result['required_pv_for_target'],22084);self.assertEqual(result['required_approved_outcomes'],11);self.assertFalse(result['partner_approved']);self.assertIsNone(result['actual_revenue_jpy'])
    def test_unknown_amount_closed_or_fx_are_excluded(self):
        for key,value in [('reward_jpy',None),('inactive',True),('currency','USD')]:
            old=self.program[key];self.program[key]=value;self.bind()
            self.assertEqual(model(self.program,self.assumptions,root=self.root,today=date(2026,10,12))['status'],'excluded');self.program[key]=old
    def test_reward_override_rejected(self):
        with self.assertRaises(ValueError):model(self.program,{**self.assumptions,'reward_jpy':9000},root=self.root,today=date(2026,10,12))
    def test_changed_amount_or_source_invalidates(self):
        self.program['reward_jpy']=10000;self.bind()
        self.assertIn('reward_does_not_match_quote',validate_program(self.program,self.root,date(2026,10,12)))
        self.program['reward_jpy']=5000;self.bind();(self.root/self.program['source_file']).write_text('different')
        self.assertIn('source_hash_mismatch',validate_program(self.program,self.root,date(2026,10,12)))
    def test_stale_review_blocks(self):self.assertIn('evidence_stale',validate_program(self.program,self.root,date(2026,12,1)))
    def test_evidence_path_escape_and_missing_review(self):
        self.program['source_file']='../private';self.bind();self.assertTrue(validate_program(self.program,self.root,date(2026,10,12)))
        self.program.pop('review_hash');self.assertTrue(validate_program(self.program,self.root,date(2026,10,12)))
    def test_actual_dataset_and_plans(self):
        programs=json.loads(Path('data/phase5/programs.json').read_text())
        eligible=[p['id'] for p in programs if not validate_program(p,today=date(2026,10,12))]
        self.assertEqual(set(eligible),{'xserver-standard','rakko-ma-listing'})
        self.assertTrue(all(p['affiliate_url'] is None for p in programs))
        keywords=json.loads(Path('data/phase5/keywords.json').read_text());plans=json.loads(Path('data/phase5/article-plans.json').read_text())
        self.assertEqual(len(keywords),20);self.assertEqual(len(plans),5)
        self.assertEqual(len({k['keyword'] for k in keywords}),20)
        self.assertTrue(all(k['search_volume'] is None and k['plan_id'] in {p['id'] for p in plans} for k in keywords))
    def test_failed_capture_does_not_confirm_anything(self):
        with patch('seo_media.phase5_research.urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect=OSError('403')
            record=acquire('fixture','https://www.xserver.ne.jp/affiliate.php',self.root/'captures')
            self.assertEqual(record['status'],'unavailable');self.assertNotIn('sha256',record)
class DecisionTests(unittest.TestCase):
    def base(self):return {'initial_spend_jpy':0,'monthly_total_spend_jpy':0,'owner_allows_live_validation':True,'personal_terms_verified':True,'serp_reviewed':True,'tracking_verified':True,'observation_days':60,'tracked_outbound_clicks':300,'approved_outcomes':0}
    def test_no_permission_preserves_site(self):
        data=self.base();data['owner_allows_live_validation']=False;result=assess(data)
        self.assertEqual(result['decision'],'offline_parallel_only');self.assertFalse(result['site_changes'])
    def test_low_sample_is_not_failure(self):
        data=self.base();data['tracked_outbound_clicks']=100;self.assertEqual(assess(data)['reason'],'insufficient_observation')
    def test_zero_outcomes_reviews_offer_not_destroys_site(self):self.assertEqual(assess(self.base())['decision'],'review_offer_or_intent')
    def test_budget_or_unknown_cost_stops(self):
        data=self.base();data['monthly_total_spend_jpy']=3001;self.assertEqual(assess(data)['decision'],'stop_additional_spend')
        data.pop('monthly_total_spend_jpy');self.assertEqual(assess(data)['reason'],'cost_unknown')
