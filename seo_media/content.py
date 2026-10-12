"""Deterministic articles with claim-level provenance and a fail-closed release gate."""
from datetime import date
from hashlib import sha256
import html
import json
from pathlib import Path
from .research import normalize, allowed

FIELDS=('resolution','recording','notifications','monthly_service','price','wifi','audio')

def fact_errors(product,field,evidence_root=Path('.'),today=None):
    today=today or date.today()
    fact=product.get('facts',{}).get(field)
    if not fact or fact.get('status')!='verified': return ['未確認: '+product['id']+'/'+field]
    errors=[]
    try:
        age=(today-date.fromisoformat(fact['verified_on'])).days
        if not 0<=age<=30: errors.append('出典の確認期限外')
        if not allowed(fact['source_url']): errors.append('公式出典ではありません')
        if fact['source_url'] not in product.get('source_urls',[product['source_url']]): errors.append('商品と出典URLが一致しません')
        relative=Path(fact['text_file'])
        root=Path(evidence_root).resolve(); path=(root/relative).resolve()
        if not path.is_relative_to(root): raise ValueError('Evidence path escaped root')
        text=path.read_text()
        captured=json.loads(path.with_suffix('.json').read_text())
        if captured.get('status')!='captured_not_reviewed' or captured.get('sha256')!=fact['sha256'] or fact['source_url'] not in (captured.get('url'),captured.get('final_url')):
            errors.append('取得記録と出典が一致しません')
        if sha256(text.encode()).hexdigest()!=fact['sha256']: errors.append('出典ファイルのハッシュ不一致')
        if not normalize(fact['quote']) or normalize(fact['quote']) not in normalize(text): errors.append('引用が出典に存在しません')
        if not fact['value'] or normalize(str(fact['value'])) not in normalize(fact['quote']): errors.append('値と引用の整合性を確認できません')
        # A reviewer checks context/negation, binds the complete claim, not just the page.
        binding={k:fact[k] for k in ('value','source_url','text_file','sha256','quote','verified_on')}
        expected=sha256(json.dumps(binding,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        if fact.get('reviewed_claim_hash')!=expected or not fact.get('reviewer'): errors.append('文脈確認の編集承認がありません')
    except (KeyError,OSError,ValueError,TypeError): errors.append('出典記録が欠落または不正')
    return errors


def link_for(product):
    if not allowed(product['source_url']): raise ValueError('Official link is not allowlisted')
    link=product.get('affiliate',{})
    if link.get('url') is not None or product.get('affiliate_url') is not None: raise ValueError('ASP links are disabled before partnership approval')
    return product['source_url'], 'official'


def render(manifest,products,evidence_root=Path(".")):
    catalog={p['id']:p for p in products}
    esc=lambda value:html.escape(str(value),quote=True)
    ready=manifest.get('editorial_review')=='approved'
    chunks=['<p>広告方針：現在ASP提携前で、アフィリエイトリンクは設置していません。</p>', ('<p class="notice">公式資料の引用に基づく編集下書きです。実機レビューではありません。未確認の料金は推測で補っていません。</p>' if ready else '<p class="notice">調査用下書きです。公式資料の確認が完了するまで公開できません。</p>')]
    for section in manifest['sections']:
        chunks.append('<h2>'+esc(section['heading'])+'</h2>')
        for paragraph in section['paragraphs']: chunks.append('<p>'+esc(paragraph)+'</p>')
    chunks.append('<h2>公式情報の確認表</h2><table><caption>確認できない項目は未確認と表示</caption><thead><tr><th>調査対象</th>')
    for field in manifest['fields']: chunks.append('<th>'+esc(manifest['labels'][field])+'</th>')
    chunks.append('</tr></thead><tbody>')
    for pid in manifest['product_ids']:
        p=catalog[pid]; url,_=link_for(p)
        chunks.append('<tr><th><a href="'+esc(url)+'">'+esc(p['name'])+('' if p.get('verified_on') else '（調査候補）')+'</a></th>')
        for field in manifest['fields']:
            fact=p['facts'][field]
            value=fact['value'] if not fact_errors(p,field,evidence_root) else '未確認'
            chunks.append('<td>'+esc(value)+'</td>')
        chunks.append('</tr>')
    chunks.append('</tbody></table><h2>出典と確認状況</h2><ul>')
    for pid in manifest['product_ids']:
        p=catalog[pid]
        chunks.append('<li><a href="'+esc(p['source_url'])+'">'+esc(p['name'])+(' 公式ページ' if p.get('verified_on') else ' 公式ページ候補')+'</a>：確認日 '+esc(p.get('verified_on') or '未確認')+'。未取得情報は推測で補完していません。</li>')
    chunks.append('</ul>')
    return {'title':manifest['title'],'keyword':manifest['keyword'],'content':''.join(chunks),'product_ids':manifest['product_ids'],'sources':[catalog[pid]['source_url'] for pid in manifest['product_ids']],'mode':'research','manifest_id':manifest['id']}


def release_report(article,manifest,products,evidence_root=Path('.')):
    errors=[]
    try:
        expected=render(manifest,products,evidence_root)
        if article!=expected: errors.append('記事と出典に紐づく構成データが一致しません')
        if manifest.get('editorial_review')!='approved': errors.append('記事全体の編集レビュー未承認')
        binding={k:v for k,v in manifest.items() if k!='reviewed_manifest_hash'}
        expected_review=sha256(json.dumps(binding,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        if manifest.get('reviewed_manifest_hash')!=expected_review or not manifest.get('editorial_reviewer'):
            errors.append('記事構成のレビュー記録が不一致または欠落')
        catalog={p['id']:p for p in products}
        for pid in manifest['product_ids']:
            p=catalog[pid]
            link_for(p)
            verified_count=0
            for field in manifest['fields']:
                fact=p.get('facts',{}).get(field,{})
                if fact.get('status')=='unknown' and fact.get('value') is None and fact.get('reason'):
                    continue  # Explicit unknown is not asserted as a fact.
                errors.extend(fact_errors(p,field,evidence_root))
                if fact.get('status')=='verified': verified_count+=1
            if verified_count==0: errors.append('確認済みの商品情報がありません: '+pid)
    except (KeyError,ValueError,TypeError) as exc: errors.append('構成またはリンク設定不正')
    return {'publishable':not errors,'errors':errors,'status':'blocked' if errors else 'editorially_verified','automatic_publication':False}


def build():
    products=json.loads(Path('data/research/products.json').read_text())
    for path in sorted(Path('content/manifests').glob('*.json')):
        manifest=json.loads(path.read_text()); article=render(manifest,products)
        output=Path('content/articles')/manifest['id']
        output.with_suffix('.json').write_text(json.dumps(article,ensure_ascii=False,indent=2))
        output.with_suffix('.html').write_text(article['content'])
        output.with_suffix('.report.json').write_text(json.dumps(release_report(article,manifest,products),ensure_ascii=False,indent=2))
        print(manifest['id'],'release blocked' if not release_report(article,manifest,products)['publishable'] else 'verified')

if __name__=='__main__': build()
