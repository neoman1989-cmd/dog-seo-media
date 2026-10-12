"""Draft-only editorial pipeline. Standard library; secrets never serialized."""
import argparse
import base64
from datetime import date
import hashlib
import html
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.URLError("Redirect refused")


def request_json(url, payload, headers=None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=60) as response:
            return json.load(response)
    except (urllib.error.URLError, ValueError) as exc:
        # Do not propagate response bodies or authentication headers.
        raise RuntimeError("Remote request failed; check credentials, network and service logs.") from None


def secure_url(url):
    parsed = urllib.parse.urlsplit(url)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def generate(brief, products, mode="mock", *, state=None, budget=None):
    selected = [p for p in products if p["category"] == brief["category"]]
    if mode == "mock":
        rows = "".join(f'<tr><th>{html.escape(p["name"])}</th><td>{html.escape("・".join(p["features"]))}</td><td>公式サイトで確認</td></tr>' for p in selected)
        body = f"""<p>広告：この記事にはアフィリエイトリンクを含む場合があります。</p>
<p>これは検証用のサンプル記事です。商品情報は架空であり、購入判断には使用できません。</p>
<h2>犬の留守番と見守りの基本</h2><p>カメラは日々の様子を確認する補助手段です。留守番時間や室温、飲み水、安全な居場所を確認し、犬の体調に合わせて環境を整えましょう。異変がある場合は獣医師へ相談してください。</p>
<h2>選び方</h2><p>通知の設定、映像の見やすさ、音声機能、録画費用を確認します。自宅の通信環境や設置場所との適合性も重要です。利用前に、犬が機器や電源コードに触れない位置へ設置してください。</p>
<h2>比較表</h2><table><caption>検証用サンプル商品の比較</caption><thead><tr><th>商品</th><th>機能</th><th>価格</th></tr></thead><tbody>{rows}</tbody></table>
<h2>購入前の確認</h2><p>価格やサービス内容は変更されます。公式の仕様、契約条件、保証、解約方法を確認してください。順位や効果を断定せず、必要な機能と総費用から選びましょう。</p>
<h2>よくある質問</h2><h3>見守り機器だけで留守番は安心ですか？</h3><p>機器だけで安全を保証することはできません。犬に合った留守番の練習や環境づくりと併用してください。</p>
<h2>出典</h2><ul>""" + "".join(f'<li><a href="{html.escape(p["source_url"], quote=True)}">{html.escape(p["name"])}</a>（未検証）</li>' for p in selected) + "</ul>"
        return {"title":brief["title"], "keyword":brief["keyword"], "content":body, "product_ids":[p["id"] for p in selected], "sources":[p["source_url"] for p in selected], "mode":"mock"}
    if mode != "live":
        raise ValueError("mode must be mock or live")
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is required for live generation")
    if not selected:
        raise ValueError("No matching products")
    for product in selected:
        if product.get("demo") or not secure_url(product.get("source_url", "")):
            raise ValueError("Replace demo products with verified HTTPS official sources before live generation")
        try:
            age = (date.today() - date.fromisoformat(product.get("verified_on") or "")).days
        except ValueError:
            raise ValueError("Product verification date is required") from None
        if not 0 <= age <= 30:
            raise ValueError("Product verification must be within 30 days")
    prompt = {"brief":brief,"products":selected,"instructions":"日本語のSEO比較記事をJSONのみで返す。title, keyword, content(HTML), product_ids, sourcesを含める。入力の公式情報のみを使う。商品・価格・体験・ランキングを創作しない。広告表示、選び方、比較表、注意点、FAQ、出典を含める。医療や安全の効果を断定しない。HTMLはscriptやイベント属性を含めない。"}
    payload = {
        "model":os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), "max_tokens":2500,
        "response_format":{"type":"json_object"},
        "messages":[{"role":"user","content":json.dumps(prompt,ensure_ascii=False)}]}
    if state is None or budget is None or state.checkpoint is None:
        raise ValueError("Live generation requires budget and durable checkpoint")
    reservation = budget.reserve(state, payload['model'], payload['messages'], payload['max_tokens'])
    result = request_json("https://api.openai.com/v1/chat/completions", payload,
        {"Authorization":"Bearer " + os.environ["OPENAI_API_KEY"]})
    budget.confirm(state, reservation, result)
    article = json.loads(result["choices"][0]["message"]["content"])
    article["mode"] = "live"
    return article


def plain(content):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", content))).strip()


def inspect(article, products, previous=()):
    errors, warnings = [], []
    content = article.get("content", "")
    title = article.get("title", "")
    text = plain(content)
    if not isinstance(title, str) or not title.strip(): errors.append("タイトルがありません")
    if len(text) < 300: errors.append("本文が短すぎます（300文字未満）")
    for token in ("<h2", "<table", "広告", "出典"):
        if token not in content: errors.append("必須要素がありません: " + token)
    if re.search(r"<(script|iframe|object|embed|form|style)\b|on\w+\s*=|javascript:|data:", content, re.I): errors.append("危険なHTML")
    for phrase in ("必ず治る", "絶対安全", "100%安全", "使ってみました"):
        if phrase in text: errors.append("根拠が必要な断定・体験: " + phrase)
    catalog = {p["id"]: p for p in products}
    ids = article.get("product_ids", [])
    sources = article.get("sources", [])
    if not ids: errors.append("比較商品がありません")
    if not sources: errors.append("出典がありません")
    for url in sources:
        if not secure_url(url): errors.append("出典は認証情報なしのHTTPS URLが必要です")
        elif html.escape(url, quote=True) not in content: errors.append("本文に出典リンクがありません")
    for pid in ids:
        p = catalog.get(pid)
        if p is None:
            errors.append("未知の商品: " + str(pid)); continue
        if p["source_url"] not in sources: errors.append("商品の公式出典がありません: " + pid)
        if p["name"] not in text: errors.append("本文に商品名がありません: " + pid)
        if p.get("demo"):
            (warnings if article.get("mode") == "mock" else errors).append("サンプル商品: " + pid)
        try:
            age = (date.today() - date.fromisoformat(p.get("verified_on") or "")).days
            if age < 0 or age > 30: errors.append("商品情報の確認日が期限外: " + pid)
        except ValueError:
            if not (p.get("demo") and article.get("mode") == "mock"): errors.append("商品情報の確認日が未設定: " + pid)
    for old in previous:
        if SequenceMatcher(None, text, plain(old.get("content", ""))).ratio() >= .85:
            errors.append("既存記事との重複が疑われます"); break
    warnings.append("出典の実在・内容一致、商品仕様、価格、独自性は編集者による確認が必要")
    return {"passed":not errors,"errors":errors,"warnings":warnings,"human_review_required":True}


def article_hash(article):
    return hashlib.sha256(json.dumps(article, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def approve_article(article, state):
    digest = article_hash(article)
    entry = state.data['articles'].get(digest)
    if entry is None or entry['article'] != article:
        raise ValueError("Article not in generation ledger")
    entry['approved_hash'] = digest
    state.save()
    return digest


def post_draft(article, products, state, mode="mock"):
    digest = article_hash(article)
    entry = state.data['articles'].get(digest)
    if entry is None or entry.get('approved_hash') != digest or entry['article'] != article:
        raise ValueError("Approval hash mismatch or missing approval")
    report = inspect(article, products)
    if not report['passed']: raise ValueError("Quality gate failed")
    destination = 'mock' if mode == 'mock' else os.getenv('WP_URL','').rstrip('/')
    key = hashlib.sha256((mode + digest).encode()).hexdigest()
    if key in state.data['posts']: raise ValueError("Already posted or unresolved posting attempt")
    payload = {"title":article["title"], "content":article["content"], "status":"draft"}
    headers = None
    if mode != 'mock':
        if mode != 'live' or article.get('mode') != 'live': raise ValueError('Only live articles may reach WordPress')
        if not secure_url(destination): raise ValueError('WP_URL must be HTTPS without embedded credentials')
        user, password = os.getenv('WP_USER'), os.getenv('WP_APP_PASSWORD')
        if not user or not password: raise ValueError('WordPress application password and user are required')
        if state.checkpoint is None: raise ValueError('Live posting requires durable checkpoint')
        headers = {'Authorization':'Basic ' + base64.b64encode(f'{user}:{password}'.encode()).decode()}
    state.data['posts'][key] = {'article_hash':digest,'status':'pending','destination':destination}
    state.save()  # intent is durable before POST; timeout/crash cannot cause automatic retry
    result = {'mock':True,'payload':payload} if mode == 'mock' else request_json(destination + '/wp-json/wp/v2/posts', payload, headers)
    if mode == 'live' and (type(result.get('id')) is not int or result.get('status') != 'draft'):
        raise ValueError('Unknown WordPress result; reconcile pending attempt manually')
    state.data['posts'][key].update(status='completed', result=result)
    state.save()
    return result


def generate_once(brief, products, state, mode='mock', budget=None):
    key = hashlib.sha256((mode + brief['keyword']).encode()).hexdigest()
    existing = [v['article'] for v in state.data['articles'].values()]
    if any(v.get('generation_key') == key for v in state.data['articles'].values()):
        return None
    if key in state.data.get('generation_attempts', {}):
        raise ValueError('Unresolved generation attempt; refusing automatic retry')
    state.data.setdefault('generation_attempts', {})[key] = 'pending'
    state.save()
    article = generate(brief, products, mode, state=state, budget=budget)
    report = inspect(article, products, existing)
    if not report['passed']: raise ValueError('Quality gate failed: ' + str(report['errors']))
    digest = article_hash(article)
    state.data['articles'][digest] = {'article':article,'generation_key':key,'report':report}
    state.data['generation_attempts'][key] = 'completed'
    state.save()
    return article


def main():
    from .state import State, initialize, git_checkpoint
    from .budget import Budget
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('init-state','generate','approve','post'))
    parser.add_argument('--mode', choices=('mock','live'), default='mock')
    parser.add_argument('--state', default='.state/ledger.json')
    parser.add_argument('--state-git-dir')
    parser.add_argument('--budget-config')
    parser.add_argument('--article')
    parser.add_argument('--output', default='output')
    args = parser.parse_args()
    if args.command == 'init-state':
        initialize(args.state); return
    if args.state_git_dir and Path(args.state).resolve() != (Path(args.state_git_dir) / '.state/ledger.json').resolve():
        parser.error('Git checkpoint must persist the exact state file at .state/ledger.json')
    state = State(args.state, git_checkpoint(args.state_git_dir) if args.state_git_dir else None)
    products = json.loads(Path('data/products.json').read_text())
    output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    with state.locked():
        if args.command == 'generate':
            budget = Budget(args.budget_config) if args.budget_config else None
            for brief in json.loads(Path('data/briefs.json').read_text()):
                article = generate_once(brief, products, state, args.mode, budget)
                if article is None:
                    print('Already generated; skipped'); continue
                target = output / ('article-' + article_hash(article) + '.json')
                target.write_text(json.dumps(article,ensure_ascii=False,indent=2))
                print(f'Generated {target}; explicit approval required')
        else:
            if not args.article: parser.error('--article is required')
            article = json.loads(Path(args.article).read_text())
            if args.command == 'approve':
                if not inspect(article, products)['passed']: raise ValueError('Quality gate failed')
                print(approve_article(article, state))
            else:
                result = post_draft(article, products, state, args.mode)
                (output / ('draft-' + article_hash(article) + '.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
