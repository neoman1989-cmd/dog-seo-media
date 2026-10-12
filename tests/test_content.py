from datetime import date
from hashlib import sha256
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from seo_media.content import fact_errors,render,release_report,link_for
from seo_media.engine import inspect,post_draft,approve_article,article_hash
from seo_media.state import State,initialize
from seo_media.research import acquire

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        text='Tapo テスト機種 解像度 2K。月額料金は未確認。'
        (self.root/'source.txt').write_text(text)
        digest=sha256(text.encode()).hexdigest()
        self.url='https://www.tp-link.com/jp/home-networking/cloud-camera/tapo-c200/'
        (self.root/'source.json').write_text(json.dumps({'status':'captured_not_reviewed','sha256':digest,'url':self.url}))
        fact={'status':'verified','value':'2K','source_url':self.url,'text_file':'source.txt','sha256':digest,'quote':'解像度 2K','verified_on':date.today().isoformat(),'reviewer':'test-reviewer'}
        self.bind(fact)
        self.product={'id':'test','name':'テスト商品（実商品ではない）','source_url':self.url,'facts':{'resolution':fact},'affiliate':{'status':'not_partnered','url':None}}
        self.manifest={'id':'test','title':'検証用','keyword':'テスト','editorial_review':'approved','product_ids':['test'],'fields':['resolution'],'labels':{'resolution':'解像度'},'sections':[{'heading':'確認方針','paragraphs':['検証用の文章。']}],'editorial_reviewer':'test reviewer'}
        self.manifest['reviewed_manifest_hash']=sha256(json.dumps(self.manifest,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    def bind(self,fact):
        fact['reviewed_claim_hash']=sha256(json.dumps({k:fact[k] for k in ('value','source_url','text_file','sha256','quote','verified_on')},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    def test_verified_quote_roundtrip(self):
        self.assertEqual(fact_errors(self.product,'resolution',self.root),[])
        article=render(self.manifest,[self.product],self.root)
        self.assertIn('<td>2K</td>',article['content'])
        self.assertTrue(release_report(article,self.manifest,[self.product],self.root)['publishable'])
    def test_changed_value_cannot_use_old_approval(self):
        self.product['facts']['resolution']['value']='4K'
        self.assertTrue(fact_errors(self.product,'resolution',self.root))
    def test_quote_not_in_source_blocked(self):
        fact=self.product['facts']['resolution']; fact['quote']='解像度 8K';fact['value']='8K'; self.bind(fact)
        self.assertTrue(fact_errors(self.product,'resolution',self.root))
    def test_source_tampering_blocked(self):
        (self.root/'source.txt').write_text('違う内容')
        self.assertTrue(fact_errors(self.product,'resolution',self.root))
    def test_context_review_missing_blocked(self):
        del self.product['facts']['resolution']['reviewer']
        self.assertTrue(fact_errors(self.product,'resolution',self.root))
    def test_unknown_is_not_rendered_as_fact(self):
        self.product['facts']['resolution'].update(status='unknown',value='4K')
        article=render(self.manifest,[self.product],self.root)
        self.assertNotIn('<td>4K</td>',article['content'])
        self.assertFalse(release_report(article,self.manifest,[self.product],self.root)['publishable'])
    def test_prose_edit_blocked(self):
        article=render(self.manifest,[self.product],self.root)
        article['content']+='<p>必ず安全です。</p>'
        self.assertFalse(release_report(article,self.manifest,[self.product],self.root)['publishable'])
    def test_unapproved_affiliate_never_rendered(self):
        self.assertEqual(link_for(self.product)[1],'official')
        self.product['affiliate']['url']='https://example.com/invented'
        with self.assertRaises(ValueError): render(self.manifest,[self.product],self.root)
    def test_official_source_mismatch(self):
        fact=self.product['facts']['resolution'];fact['source_url']='https://www.furbo.com/jp/';self.bind(fact)
        self.assertTrue(fact_errors(self.product,'resolution',self.root))
    def test_failed_acquisition_never_marks_verified(self):
        with patch('seo_media.research.urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect=OSError('403 Forbidden')
            record=acquire(self.product,self.root/'captures')
            self.assertEqual(record['status'],'unavailable')
            self.assertNotIn('sha256',record)
    def test_unverified_live_article_cannot_post(self):
        article={'mode':'live','title':'未確認','content':'<p>未確認</p>','keyword':'検証','sources':[],'product_ids':[]}
        path=self.root/'state.json';initialize(path)
        with State(path,lambda:None).locked() as state:
            state.data['articles'][article_hash(article)]={'article':article}
            approve_article(article,state)
            with patch('seo_media.engine.request_json') as send:
                with self.assertRaises(ValueError): post_draft(article,[],state,'live')
                send.assert_not_called()
    def test_manifest_changed_after_review_is_blocked(self):
        self.manifest['sections'][0]['paragraphs']=['根拠のない追記']
        article=render(self.manifest,[self.product],self.root)
        self.assertFalse(release_report(article,self.manifest,[self.product],self.root)['publishable'])

    def test_import_requires_checked_sources_and_separate_approval(self):
        from seo_media.engine import main
        path=self.root/'state.json';initialize(path)
        article_file=Path('content/articles/camera-selection.json')
        with patch('sys.argv',['engine','import-article','--state',str(path),'--article',str(article_file),'--products','data/research/products.json','--output',str(self.root/'output')]):
            main()
        ledger=json.loads(path.read_text())
        entry=next(iter(ledger['articles'].values()))
        self.assertNotIn('approved_hash',entry)
        self.assertEqual(ledger['posts'],{})
        self.assertEqual(ledger['requests'],{})

    def test_three_repository_drafts_have_consistent_sources(self):
        products=json.loads(Path('data/research/products.json').read_text())
        for path in Path('content/manifests').glob('*.json'):
            manifest=json.loads(path.read_text()); article=render(manifest,products)
            self.assertTrue(release_report(article,manifest,products)['publishable'])
            self.assertTrue(inspect(article,products)['passed'])

if __name__=='__main__': unittest.main()
