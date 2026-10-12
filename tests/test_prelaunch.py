import unittest
from seo_media.prelaunch import check,FLAGS
class PrelaunchTests(unittest.TestCase):
    def test_missing_owner_approval_blocks(self):self.assertFalse(check({})['ready_for_owner_review'])
    def test_upper_limits_and_no_side_effects(self):
        config={k:True for k in FLAGS};config.update(initial_cost_jpy=30000,monthly_total_cost_jpy=3000)
        result=check(config);self.assertTrue(result['ready_for_owner_review']);self.assertFalse(result['publication_performed'])
        config['monthly_total_cost_jpy']=3001;self.assertFalse(check(config)['ready_for_owner_review'])
