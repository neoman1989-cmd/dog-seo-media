# 出典と確認範囲

取得は公開ページのGETのみ。ログイン、フォーム送信、ASP登録、外部アカウント作成、広告URLクリック、有料APIを実施していない。ネットワーク設定の公式調査ドメイン追加は下書きへ保存したが、環境スナップショットの公開は行っていない。

## 主な公開資料

- エックスサーバー: https://www.xserver.ne.jp/affiliate.php — A8広告とプラン別成約報酬。5,000/7,500/10,000円の表を確認。ページのA8統計には2024年の注記もあり、公開報酬表を現行の本人ASP条件と同一視しない。
- ConoHa: https://www.conoha.jp/affiliate/ — WINGパック/通常支払いの表、利用状況次第で額と承認条件が変動するという注意、公式「ワプ活」記事の紹介。
- ラッコID: https://rakkoid.com/affiliate/ — M&A掲載開始2,750円、契約割合式、30日計測、条件達成後の確定、出金220円等。QA一覧 https://rakkoid.com/knowledge/qa/affiliate-qa/ も取得。個々のQA本文・本人適格性まで確認したとは扱わない。
- Shopify: https://www.shopify.com/jp/affiliates — 有料プラン・最大150USD・地域差。日本向け確定額は不明。
- freee: https://www.freee.co.jp/partner/ — SA/VARと望ましい営業/コンサル実績、新規募集停止。一般のSEOアフィリエイト案件と別制度。
- Chatwork: https://go.chatwork.com/ja/partner/ — 販売パートナー紹介。一般メディア向け固定報酬は未確認。
- FPC: https://www.fpc-pet.co.jp/ — ペット保険商品・代理店募集。アフィリエイト報酬ではない。
- Furbo: https://furbo.com/jp/products/furbo-mini-360 — 製品・購入者契約を確認。紹介者の報酬を確認したものではない。

Notionの https://www.notion.com/affiliates は403。A8公開キャンペーン候補は404。未取得情報は記憶や別サイトの古い単価で埋めない。具体的なペットフード/シッター案件を発見したとは扱わない。

取得本文と成否/URL/日時はdata/phase5/sources。確認済み報酬レコードはprograms.jsonに引用・SHA-256・レビューを保存。再取得は `python -m seo_media.phase5_research`。取得成功だけで報酬を自動承認しない。本文変更や30日期限でモデルから除外する。旧本文がディスクに残っても最新取得が失敗ならモデルは拒否する。

## 検索観測

data/phase5/search-observations.json。日本Googleを6ジャンルで取得したが有機検索結果本文なし。Bing代替も対象と無関係な内容が含まれて不採用。順位・検索量・競争難易度はnullのまま。以前のブラウザCA問題を証明書検証無効化で回避しない。

競合として言えることは、公式メーカーが運用解説を提供していることまで。Google上位、参入容易、低競争などは未確認。正常な日本Googleを見られる通常ブラウザで20語を複数日に観測することが次の調査条件。検索結果を得られないことは需要ゼロの証拠ではない。
