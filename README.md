# 犬の留守番ガイド / dog-seo-media

日本語SEOアフィリエイトメディアの開発用基盤です。WordPressクラシックテーマとPythonの記事生成・検査・下書き投稿を収録しています。初期状態はモックのみで、外部APIへの送信・公開・課金はありません。

## すぐ試す

Python 3.11以上（検証環境は3.12）。外部Python依存はありません。

```bash
cd /workspace/dog-seo-media
python -m unittest discover -s tests -v
python -m seo_media.engine init-state
python -m seo_media.engine generate --mode mock
```

`output/` に記事JSONを生成し、検査結果と履歴は `.state/ledger.json` に保存します。生成コマンドから投稿は行いません。承認と投稿の手順は[セットアップ](docs/setup.md)を参照してください。サンプル商品は架空です。公開・購入判断に使わないでください。再実行時は状態台帳で生成済みキーワードをスキップします。別のoutputを指定しても再生成しません。類似本文は品質検査で停止します。既存履歴を削除して再試行しないでください。

## 実装

- `wordpress/dog-seo/`: スマホ対応トップ、記事、固定ページ、記事一覧、横スクロール比較表、広告表示、更新日、編集方針。
- `wordpress/comparison-template.html`: WordPressエディター用比較記事テンプレート。
- `seo_media/engine.py`: モック／OpenAI生成、商品・出典・期限・重複・HTML・最低品質検査、REST API下書き投稿。
- `data/`: キーワードブリーフと商品台帳。実商品の公式資料に置換して使います。
- `.github/workflows/editorial.yml`: 月曜08:00 JST（日曜23:00 UTC）にモック生成、テスト、レビュー用artifact保存。履歴は専用の `editorial-state` ブランチで実行間に保持。手動実行も可能。自動公開なし。

検査は出典URLと台帳の整合性を確認しますが、URLの実在や内容の真偽を自動保証しません。実投稿前に公式情報・価格・機能・独自性を編集者が確認してください。ライブ生成にはAPI利用料が発生します。今回ライブAPIは使用していません。OpenAIの月額上限は3,000円で、確認済み料金・為替・既存支出の上限が未設定なら停止します。[予算と永続状態の仕様](docs/safety.md)を参照してください。

詳細: [セットアップ](docs/setup.md)、[サイト設計・事業計画](docs/site-plan.md)、[運用・品質管理](docs/editorial.md)。

WordPress実表示の再現手順・スクリーンショット・検証結果: [ローカル検証](docs/wordpress-validation.md)。
