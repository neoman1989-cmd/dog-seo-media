import unittest
from datetime import date
from seo_media.monetization import estimate
from seo_media.links import resolve,approval_digest
class ProfitTests(unittest.TestCase):
    def scenario(self):return {'monthly_pv':10000,'outbound_ctr':.1,'conversion_rate':.02,'approval_rate':.8,'reward_jpy':500,'monthly_cost_jpy':3000}
    def test_profit_and_needed_traffic(self):
        result=estimate(self.scenario());self.assertEqual(result['profit_jpy'],'5000.0000');self.assertEqual(result['required_pv_for_target'],66250)
    def test_zero_reward_does_not_invent_viability(self):
        scenario=self.scenario();scenario['reward_jpy']=0;self.assertIsNone(estimate(scenario)['required_pv_for_target'])
    def test_invalid_or_over_budget(self):
        for field,value in [('conversion_rate',1.1),('monthly_cost_jpy',3001),('reward_jpy','NaN')]:
            s=self.scenario();s[field]=value
            with self.assertRaises(ValueError):estimate(s)
class LinkTests(unittest.TestCase):
    def setUp(self):
        self.product={'id':'fixture','source_url':'https://official.example/product','affiliate':{'status':'approved','product_id':'fixture','asp':'test-fixture-only','approval_id':'fixture-only','owner_reviewer':'fixture','approved_on':'2026-10-01','expires_on':'2026-10-31','url':'https://ads.example/test-only'}}
        record=self.product['affiliate'];record['owner_approval_hash']=approval_digest(record)
        self.policy={'affiliate_enabled':True,'allowed_affiliate_hosts':['ads.example']}
    def test_disabled_uses_normal_link(self):self.assertEqual(resolve(self.product)['type'],'official')
    def test_explicit_valid_approval_switch(self):
        result=resolve(self.product,self.policy,date(2026,10,12));self.assertEqual(result['type'],'affiliate');self.assertIn('sponsored',result['rel'])
    def test_changed_url_or_expiry_falls_back(self):
        self.product['affiliate']['url']='https://ads.example/modified'
        self.assertEqual(resolve(self.product,self.policy,date(2026,10,12))['type'],'official')
        self.assertEqual(resolve(self.product,self.policy,date(2026,11,1))['type'],'official')
    def test_unknown_host_and_wrong_product_fall_back(self):
        self.policy['allowed_affiliate_hosts']=[];self.assertEqual(resolve(self.product,self.policy,date(2026,10,12))['type'],'official')
        self.product['affiliate']['product_id']='wrong';self.assertEqual(resolve(self.product,self.policy,date(2026,10,12))['type'],'official')
