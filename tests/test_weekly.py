import unittest
from seo_media.weekly import report
class WeeklyTests(unittest.TestCase):
    def row(self,**values):return {'page':'https://example.invalid/guide/','clicks':10,'impressions':200,'position':'12','ctr':'.05',**values}
    def test_review_recommendation_does_not_rewrite(self):
        result=report([self.row()],[self.row(clicks=5,ctr='.025')]);self.assertEqual(result['pages'][0]['click_delta'],5);self.assertFalse(result['automatic_rewrite'])
    def test_low_data_and_zero_ctr(self):
        result=report([self.row(impressions=0,ctr=None,clicks=0)],[]);self.assertEqual(result['pages'][0]['action'],'insufficient_data');self.assertIsNone(result['pages'][0]['ctr_delta'])
    def test_duplicate_exports_rejected(self):
        with self.assertRaises(ValueError):report([self.row(),self.row()],[])
