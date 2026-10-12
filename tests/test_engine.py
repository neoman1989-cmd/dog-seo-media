from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from seo_media.engine import generate, generate_once, inspect, post_draft, approve_article, article_hash, main
from seo_media.state import State, initialize
from seo_media.budget import Budget

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'ledger.json'
        initialize(self.path)
        self.products = json.loads(Path('data/products.json').read_text())
        self.brief = json.loads(Path('data/briefs.json').read_text())[0]
        self.article = generate(self.brief, self.products)
        self.now = datetime(2026,10,12,0,tzinfo=timezone.utc)
        self.cost = Path(self.tmp.name)/'cost.json'
        self.config = {'month_jst':'2026-10','observed_at':self.now.isoformat(),'rates_valid_until':'2026-10-13T00:00:00+00:00','exclusive_project':True,'month_spend_jpy_upper_bound':'0','usd_jpy_upper_bound':'200','models':{'gpt-4.1-mini':{'input_usd_per_million':'1','output_usd_per_million':'4'}}}
        self.save_config()

    def save_config(self): self.cost.write_text(json.dumps(self.config))
    def state(self): return State(self.path, checkpoint=lambda: None)
    def budget(self): return Budget(self.cost, now=self.now)
    def live_products(self):
        for p in self.products: p.update(demo=False,verified_on=date.today().isoformat())
    def register(self, state, article=None):
        article = article or self.article
        state.data['articles'][article_hash(article)] = {'article':article}
        approve_article(article, state)

    def test_mock_quality_and_approved_draft(self):
        with self.state().locked() as state:
            self.register(state)
            self.assertEqual(post_draft(self.article,self.products,state)['payload']['status'],'draft')

    def test_duplicate_content_blocked(self):
        self.assertFalse(inspect(self.article,self.products,[self.article])['passed'])

    def test_missing_source_unknown_product(self):
        self.article['sources']=[]; self.article['product_ids'].append('unknown')
        self.assertFalse(inspect(self.article,self.products)['passed'])

    def test_unsafe_html(self):
        self.article['content'] += '<img src=x onerror="alert(1)">'
        self.assertFalse(inspect(self.article,self.products)['passed'])

    def test_demo_cannot_be_live(self):
        self.article['mode']='live'
        self.assertFalse(inspect(self.article,self.products)['passed'])

    def test_stale_products(self):
        self.products[0].update(demo=False,verified_on='2020-01-01')
        self.assertFalse(inspect(self.article,self.products)['passed'])

    def test_missing_key(self):
        with patch.dict(os.environ,{},clear=True), self.assertRaises(ValueError): generate(self.brief,self.products,'live')

    def test_demo_rejected_before_call(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-only'}), patch('seo_media.engine.request_json') as send:
            with self.assertRaises(ValueError): generate(self.brief,self.products,'live')
            send.assert_not_called()

    def test_live_generation_with_usage(self):
        self.live_products()
        response={'choices':[{'message':{'content':json.dumps(self.article)}}], 'usage':{'prompt_tokens':500,'completion_tokens':1000}}
        with self.state().locked() as state, patch.dict(os.environ,{'OPENAI_API_KEY':'test-only'}), patch('seo_media.engine.request_json',return_value=response):
            self.assertEqual(generate(self.brief,self.products,'live',state=state,budget=self.budget())['mode'],'live')
            self.assertEqual(next(iter(state.data['requests'].values()))['status'],'confirmed')

    def test_live_requires_durable_budget(self):
        self.live_products()
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-only'}), patch('seo_media.engine.request_json') as send:
            with self.assertRaises(ValueError): generate(self.brief,self.products,'live')
            send.assert_not_called()

    def test_live_post_draft_and_persistent_dedup(self):
        self.live_products(); self.article['mode']='live'
        with self.state().locked() as state:
            self.register(state)
            with patch.dict(os.environ,{'WP_URL':'https://wp.example','WP_USER':'editor','WP_APP_PASSWORD':'test-only'}), patch('seo_media.engine.request_json',return_value={'id':10,'status':'draft'}) as send:
                post_draft(self.article,self.products,state,'live')
                self.assertEqual(send.call_args.args[1]['status'],'draft')
        with self.state().locked() as state, patch.dict(os.environ,{'WP_URL':'https://WP.example/'}), patch('seo_media.engine.request_json') as send:
            with self.assertRaises(ValueError): post_draft(self.article,self.products,state,'live')
            send.assert_not_called()

    def test_unapproved_or_modified_cannot_post(self):
        with self.state().locked() as state:
            with self.assertRaises(ValueError): post_draft(self.article,self.products,state)
            self.register(state)
            self.article['title'] += '変更'
            with self.assertRaises(ValueError): post_draft(self.article,self.products,state)

    def test_quality_rechecked_after_approval(self):
        with self.state().locked() as state:
            self.register(state)
            self.products=[]
            with self.assertRaises(ValueError): post_draft(self.article,self.products,state)

    def test_timeout_post_is_never_retried(self):
        self.live_products(); self.article['mode']='live'
        credentials={'WP_URL':'https://wp.example','WP_USER':'editor','WP_APP_PASSWORD':'test-only'}
        with self.state().locked() as state:
            self.register(state)
            with patch.dict(os.environ,credentials), patch('seo_media.engine.request_json',side_effect=RuntimeError('timeout')):
                with self.assertRaises(RuntimeError): post_draft(self.article,self.products,state,'live')
        with self.state().locked() as state, patch.dict(os.environ,credentials), patch('seo_media.engine.request_json') as send:
            with self.assertRaises(ValueError): post_draft(self.article,self.products,state,'live')
            send.assert_not_called()

    def test_checkpoint_failure_prevents_post(self):
        with self.state().locked() as state:
            self.register(state)
            state.checkpoint=lambda: (_ for _ in ()).throw(RuntimeError('persistence failed'))
            with patch('seo_media.engine.request_json') as send:
                with self.assertRaises(RuntimeError): post_draft(self.article,self.products,state)
                send.assert_not_called()

    def test_generation_dedup_across_outputs(self):
        with self.state().locked() as state: self.assertIsNotNone(generate_once(self.brief,self.products,state))
        with self.state().locked() as state, patch('seo_media.engine.generate') as gen:
            self.assertIsNone(generate_once(self.brief,self.products,state)); gen.assert_not_called()

    def test_generation_failure_not_retried(self):
        with self.state().locked() as state, patch('seo_media.engine.generate',side_effect=RuntimeError()):
            with self.assertRaises(RuntimeError): generate_once(self.brief,self.products,state)
        with self.state().locked() as state, patch('seo_media.engine.generate') as gen:
            with self.assertRaises(ValueError): generate_once(self.brief,self.products,state)
            gen.assert_not_called()

    def test_budget_limit_and_unknown_configuration(self):
        self.config['month_spend_jpy_upper_bound']='2999'; self.save_config()
        with self.state().locked() as state, self.assertRaises(ValueError): self.budget().reserve(state,'gpt-4.1-mini',[],2500)
        self.config['month_spend_jpy_upper_bound']=None; self.save_config()
        with self.state().locked() as state, self.assertRaises(ValueError): self.budget().reserve(state,'gpt-4.1-mini',[],2500)

    def test_budget_unknown_model_and_stale_baseline(self):
        with self.state().locked() as state, self.assertRaises(KeyError): self.budget().reserve(state,'unknown',[],2500)
        self.config['observed_at']='2026-10-01T00:00:00+00:00'; self.save_config()
        with self.state().locked() as state, self.assertRaises(ValueError): self.budget().reserve(state,'gpt-4.1-mini',[],2500)

    def test_missing_usage_blocks_next_request(self):
        with self.state().locked() as state:
            budget=self.budget(); key=budget.reserve(state,'gpt-4.1-mini',[],2500)
            with self.assertRaises(ValueError): budget.confirm(state,key,{})
        with self.state().locked() as state, self.assertRaises(ValueError): self.budget().reserve(state,'gpt-4.1-mini',[],2500)

    def test_reservations_accumulate_across_restart(self):
        self.config['month_spend_jpy_upper_bound']='2997.18'; self.save_config()
        with self.state().locked() as state:
            budget=self.budget(); key=budget.reserve(state,'gpt-4.1-mini',[],2500)
            budget.confirm(state,key,{'usage':{'prompt_tokens':0,'completion_tokens':0}})
            self.assertEqual(state.data['requests'][key]['reserved_jpy'],'2.82')
        with self.state().locked() as state, self.assertRaises(ValueError):
            self.budget().reserve(state,'gpt-4.1-mini',[],2500)

    def test_expired_rates_invalid_fx_or_shared_project(self):
        for field,value in [('rates_valid_until','2026-10-11T00:00:00+00:00'),('usd_jpy_upper_bound','NaN'),('exclusive_project',False)]:
            old=self.config[field]; self.config[field]=value; self.save_config()
            with self.state().locked() as state, self.assertRaises(ValueError): self.budget().reserve(state,'gpt-4.1-mini',[],2500)
            self.config[field]=old

    def test_budget_checkpoint_failure_prevents_api(self):
        self.live_products()
        with self.state().locked() as state, patch.dict(os.environ,{'OPENAI_API_KEY':'test-only'}), patch('seo_media.engine.request_json') as send:
            state.checkpoint=lambda: (_ for _ in ()).throw(RuntimeError('push failed'))
            with self.assertRaises(RuntimeError): generate(self.brief,self.products,'live',state=state,budget=self.budget())
            send.assert_not_called()

    def test_unknown_usage_after_network_failure_remains_reserved(self):
        self.live_products()
        with self.state().locked() as state, patch.dict(os.environ,{'OPENAI_API_KEY':'test-only'}), patch('seo_media.engine.request_json',side_effect=RuntimeError('timeout')):
            with self.assertRaises(RuntimeError): generate(self.brief,self.products,'live',state=state,budget=self.budget())
        with self.state().locked() as state:
            self.assertEqual(next(iter(state.data['requests'].values()))['status'],'unknown')
            with self.assertRaises(ValueError): self.budget().reserve(state,'gpt-4.1-mini',[],2500)

    def test_usage_exceeding_estimate_stops(self):
        with self.state().locked() as state:
            budget=self.budget(); key=budget.reserve(state,'gpt-4.1-mini',[],2500)
            with self.assertRaises(ValueError): budget.confirm(state,key,{'usage':{'prompt_tokens':100000,'completion_tokens':1000}})
            self.assertEqual(state.data['requests'][key]['status'],'unknown')

    def test_previous_month_baseline_rejected_at_boundary(self):
        self.config.update(month_jst='2026-11',observed_at='2026-10-31T14:59:00+00:00',rates_valid_until='2026-11-02T00:00:00+00:00'); self.save_config()
        with self.state().locked() as state, self.assertRaises(ValueError):
            Budget(self.cost,datetime(2026,10,31,15,tzinfo=timezone.utc)).reserve(state,'gpt-4.1-mini',[],2500)

    def test_jst_month_boundary(self):
        self.config.update(month_jst='2026-11', observed_at='2026-10-31T15:00:00+00:00',rates_valid_until='2026-11-02T00:00:00+00:00'); self.save_config()
        with self.state().locked() as state:
            budget=Budget(self.cost,datetime(2026,10,31,15,tzinfo=timezone.utc))
            key=budget.reserve(state,'gpt-4.1-mini',[],2500)
            self.assertEqual(state.data['requests'][key]['month'],'2026-11')

    def test_cli_separates_generation_approval_post(self):
        output=Path(self.tmp.name)/'output'
        base=['--state',str(self.path),'--output',str(output)]
        with patch('sys.argv',['engine','generate',*base]): main()
        article=next(output.glob('article-*.json'))
        self.assertEqual(len(list(output.glob('draft-*'))),0)
        with patch('sys.argv',['engine','post',*base,'--article',str(article)]), self.assertRaises(ValueError): main()
        with patch('sys.argv',['engine','approve',*base,'--article',str(article)]): main()
        with patch('sys.argv',['engine','post',*base,'--article',str(article)]): main()
        self.assertEqual(len(list(output.glob('draft-*'))),1)

if __name__=='__main__': unittest.main()
