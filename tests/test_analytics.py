from pathlib import Path
import tempfile
import unittest
from seo_media.analytics import import_search_console
class AnalyticsTests(unittest.TestCase):
    def read(self,data):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'data.csv';file.write_text(data)
            return import_search_console(file,'example.com')
    def test_import_is_offline(self):
        rows=self.read('page,clicks,impressions,position\nhttps://example.com/guide/,2,100,12.5\n')
        self.assertEqual(rows[0]['ctr'],'0.02')
    def test_zero_impressions(self):
        self.assertIsNone(self.read('page,clicks,impressions,position\nhttps://example.com/guide/,0,0,0\n')[0]['ctr'])
    def test_wrong_host_and_inconsistent_metrics(self):
        for row in ('https://other.example/guide/,1,1,1','https://example.com/guide/,2,1,1','https://example.com/?email=person,1,1,1'):
            with self.assertRaises(ValueError):self.read('page,clicks,impressions,position\n'+row+'\n')
