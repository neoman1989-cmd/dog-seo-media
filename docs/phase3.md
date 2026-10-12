# Phase 3: 出典に基づくコンテンツ基盤

mainの69f29b6（PR #2）から `feat/phase3-content` を作成。調査日は2026-10-12 JST。実機購入・使用・ASP提携・有料API・本番公開は行っていない。

## 商品台帳と確認範囲

実データは `data/research/products.json`。mock用 `data/products.json` と分離してActionsの安全なサンプル実行を維持する。

|商品（取得時の表示）|公式解像度|ローカル保存|有償クラウド|本体価格|
|---|---|---|---|---|
|Tapo C200 V5表示|1080p（1920×1080px）|microSD最大512GB、カード別売り|Tapo Care|未取得|
|Tapo C210 V3表示|2K 3MP（2304×1296px）|同上|Tapo Care|未取得|
|Tapo C220|2K QHD 4MP（2560×1440px）|同上|Tapo Care|メーカー希望小売価格：本体5,880円（税込み）|
|Tapo C225|2K QHD 4MP（2560×1440px）|同上|Tapo Care|未取得|
|Tapo C120|2K QHD 4MP（2560×1440px）|同上|Tapo Care|未取得|

同一メーカー5商品を対象にしており、市場全体のおすすめ順位を意味しない。ペット専用機種と断定せず、室内見守り候補として比較する。モデル名は日本公式本文で確認した。国内在庫・購入条件、旧ハードウェア版への適用、実機画質・通知精度は未検証。

通知は各ページのシステム通知とTapo Care利用条件をそのまま引用。全商品で公式仕様に2.4GHz Wi-Fiと双方向通話の記載を確認。カード互換性や全録画条件は購入前に公式注意事項も確認する。円建ての日本向けTapo Care料金は公開本文から取得できず、月額・年額を創作しない。C220の希望小売価格を実売価格として扱わない。価格の無い商品を0円扱いしない。

公式URLは台帳と各記事の出典欄を参照。取得本文は `data/evidence/*.txt`、取得日時・URL・本文SHA-256は隣接JSON。各事実に引用、表示値、確認日、出典ハッシュ、文脈確認者と確認済みclaimハッシュを保存。引用の解釈に疑義がある場合はunknownへ戻し、再レビューする。全文スナップショットは監査用で、記事には必要な仕様欄だけを引用する。

## キーワード10件

`data/research/keywords.json` に検索意図・購買意欲の定性仮説、記事構成、優先度を保存。検索ボリュームはnull。

Googleの10検索はHTTP 200で取得できたが、本文はJavaScriptへの誘導だけで有機検索結果を含まなかった。Chromiumによる検索は証明書信頼エラーで中止し、TLS検証を無効化していない。SERPの競合URL・順位・難易度は未取得。公式・EC・比較メディア・個人実機レビューを調査対象として設計したが、実在の上位競合と断定していない。結果は `data/research/serp-attempts.json`。競合評価は残課題。

## 3記事

- 犬の留守番用ペットカメラの選び方：購入前に確認したい項目
- ペットカメラの月額費用を確認する方法：本体代と録画料金を分けて考える
- ペットカメラの録画を選ぶ前に：保存先・保存期間・通知を確認する

構成と編集本文は `content/manifests/`、JSON・HTML・品質レポートは `content/articles/`。生成は有料APIを使わない決定的レンダラー。確認済み項目は引用の範囲だけで表示し、未知項目は未確認とする。使用体験・実機評価・ランキングは含まない。執筆者欄や独自画像、実機レビューは今後必要な編集拡充であり、実装済みの体験としない。

```bash
python -m seo_media.research  # 無料の公式ページ再取得。取得だけでは事実の承認を付与しない
python -m seo_media.content  # 保存台帳と構成から記事・レポートを再構築
python -m unittest discover -s tests -v
```

再取得で本文ハッシュが変わると引用承認は失効する。確認期間は30日。ページの自動抽出だけでは意味・ハードウェア版・地域の一致を保証しないため、編集者が文脈を照合しclaimハッシュを付与する。レビュー後に本文・構成を変更するとmanifestハッシュ照合で停止する。構成のレビュー記録は今回Codexが公式本文と照合した記録であり、独立した専門家・実機レビューではない。

## 公開停止ゲート

非mockの記事にはmanifest、編集レビュー、保存本文、引用・値・商品URL・確認日・ハッシュの一致が必要。未確認の値を断定したもの、出典変更後の記事、未承認構成、本文への追記は拒否。unknownかつvalue:nullかつ理由を明示した項目は「未確認」とのみ表示でき、料金を断定していないため許容する。各商品に少なくとも1つの検証済み項目が無ければ停止。アフィリエイトURLは提携前のため全て禁止する。

レポートのpublishableは出典整合検査の結果であり、本番公開の許可ではない。WordPress投稿statusは常にdraft。外部送信には別の手動ハッシュ承認と耐久状態保存が引き続き必要。現行CLIに `--products data/research/products.json` と `import-article --article ...` を追加し、出典検査済みJSONを台帳へ登録可能。importは承認・投稿をしない。本作業では本番投稿コマンドを実行していない。

## リンク管理

商品台帳のsource_urlは通常の公式リンク。affiliateにはnot_partnered、ASP名・承認ID・URLはnullを保存。URLを創作しない。将来はASP側の提携承認記録と実際に提供されたURLを別フィールドで保存し、承認日・対象商品・有効期限と広告表示を確認する。現段階ではURLを設定するとレンダラーが停止し、ASPリンクを設置できない。

## WordPress検証

```bash
# 既存のvalidation/.envを使用。初回はpython validation/init.pyでローカル資格情報を作成。
python -m seo_media.content
docker compose --project-name dog-media-validation --env-file validation/.env -f validation/compose.yml up -d wordpress
docker compose --project-name dog-media-validation --env-file validation/.env -f validation/compose.yml run --rm --entrypoint sh cli /fixtures/phase3-seed.sh > artifacts/phase3/wp-posts.json
cd validation/browser
npm ci
npx playwright test --config phase3.config.js
```

このクラウドのループバック転送・Chromium設定はdocs/wordpress-validation.mdを参照。認証付きプレビューだけを使用し、記事3件はdraftのまま。匿名アクセス404を検証。テストはローカル専用資格情報を読み込むが値をログ・Gitに出さず、ログイン画面は撮影しない。スクリーンショットと結果はartifacts/phase3。実機iOSや検索エンジン評価を確認したものではない。

## 予算・制約

今回の外部支払い・API利用料金は0円。既存クラウドの提供リソースと無料の公式ページ・ローカルテストのみ使用。初期30,000円／月額3,000円の枠を追加消費していない。APIは従来の目安500円の枠内で計画し、将来の契約・利用は別途確認。ASP・解析サービスの登録、GA4タグ設置、ドメイン購入、環境の公開、本番公開は行っていない。

公式サイト調査のネットワーク追加は環境設定の下書きに保存した。実行中に公式ドメインのアクセス成功を確認したが、環境スナップショットの公開を実施・確認したものではない。

## 今回の検証結果

Python 50テスト成功。出典・値の改変、manifestレビュー不一致、ASP URL混入、未検証記事の送信拒否、検証済みJSONの未承認インポート、CSV処理を検証。WordPressプレビュー9テスト成功（3記事×320/375/1280px）。匿名閲覧404、下書き状態、表5商品、公式リンク、ページ全体の横はみ出しなしを確認。git diff --check成功。

GitHub Actionsの実行結果取得はGitHub APIのForbiddenで拒否され、GitHub-hostedの稼働は未確認。ローカルで既存モック・状態保存テストは成功。本作業ではActionsをリモート起動していない。PR作成もGitHub API権限が必要。
