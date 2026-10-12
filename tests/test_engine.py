import copy
from datetime import date
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from seo_media.engine import generate, inspect, post_draft, main

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.products = json.loads(Path('data/products.json').read_text())
        self.brief = json.loads(Path('data/briefs.json').read_text())[0]
        self.article = generate(self.brief, self.products)

    def test_mock_quality_and_draft(self):
        report = inspect(self.article, self.products)
        self.assertTrue(report['passed'], report)
        self.assertTrue(report['human_review_required'])
        self.assertEqual(post_draft(self.article, report)['payload']['status'], 'draft')

    def test_duplicate_blocked(self):
        self.assertFalse(inspect(self.article, self.products, [self.article])['passed'])

    def test_missing_source_and_unknown_product(self):
        self.article['sources'] = []
        self.article['product_ids'].append('unknown')
        self.assertFalse(inspect(self.article, self.products)['passed'])

    def test_unsafe_html(self):
        self.article['content'] += '<img src=x onerror="alert(1)">'
        self.assertFalse(inspect(self.article, self.products)['passed'])

    def test_demo_cannot_be_live(self):
        self.article['mode'] = 'live'
        self.assertFalse(inspect(self.article, self.products)['passed'])

    def test_stale_products(self):
        self.products[0]['demo'] = False
        self.products[0]['verified_on'] = '2020-01-01'
        self.assertFalse(inspect(self.article, self.products)['passed'])

    def test_failed_quality_cannot_post(self):
        with self.assertRaises(ValueError): post_draft(self.article, {'passed':False})

    def test_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError): generate(self.brief, self.products, 'live')

    def test_live_demo_rejected_before_api_call(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY':'test-only'}), patch('seo_media.engine.request_json') as send:
            with self.assertRaises(ValueError): generate(self.brief, self.products, 'live')
            send.assert_not_called()

    def test_verified_live_generation(self):
        for product in self.products:
            product['demo'] = False
            product['verified_on'] = date.today().isoformat()
        response = {'choices':[{'message':{'content':json.dumps(self.article)}}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY':'test-only'}), patch('seo_media.engine.request_json', return_value=response):
            article = generate(self.brief, self.products, 'live')
            self.assertEqual(article['mode'], 'live')
            self.assertTrue(inspect(article, self.products)['passed'])

    def test_live_post_always_draft(self):
        self.article['mode'] = 'live'
        with patch.dict(os.environ, {'WP_URL':'https://wordpress.example','WP_USER':'editor','WP_APP_PASSWORD':'test-only'}), patch('seo_media.engine.request_json', return_value={'id':10}) as send:
            post_draft(self.article, {'passed':True}, 'live')
            self.assertEqual(send.call_args.args[1]['status'], 'draft')
            self.assertEqual(send.call_args.args[0], 'https://wordpress.example/wp-json/wp/v2/posts')

    def test_mock_cannot_reach_live_wp(self):
        with self.assertRaises(ValueError): post_draft(self.article, {'passed':True}, 'live')

    def test_cli_and_repeat_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('sys.argv', ['engine','--mode','mock','--post','--output',directory]): main()
            self.assertEqual(len(list(Path(directory).glob('draft-*.json'))), 1)
            with patch('sys.argv', ['engine','--mode','mock','--output',directory]):
                with self.assertRaises(SystemExit): main()

if __name__ == '__main__': unittest.main()
