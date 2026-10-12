# セットアップ

## ローカル／クラウド

Python 3.11+のみでモック開発可能。依存インストール不要。リポジトリのディレクトリでREADMEのテスト・生成コマンドを実行する。環境変数はOSやCIから渡す（`.env`の自動読込は実装していない）。仮想環境は任意。

## WordPress

WordPress 6.4+、PHP 8.1+、HTTPSを用意する。今回サーバー契約・購入・公開は実施しない。

1. `wordpress/dog-seo` を検証用WordPressの `wp-content/themes/dog-seo` にコピーし有効化。
2. 設定→表示設定は最新の投稿を表示。テーマのfront-page.phpがホームを表示する。
3. カテゴリ「留守番」「ペットカメラ」「自動給餌器」「関連サービス」を作成しメニューに設定。
4. 編集方針、運営者情報、問い合わせ、プライバシーポリシー、広告方針を固定ページとして作成。公開サイトでの広告・解析導入に合わせポリシーを更新。
5. 比較テンプレートをコードエディターに貼り付け、確認済み実データで下書き作成。
6. 検証用の投稿可能な専用ユーザーにアプリケーションパスワードを作成。管理者の認証を共有しない。

## 実APIへの移行（今回未実行）

`data/products.json` のdemo商品を削除し、実商品のid/name/category/features/price_yen/source_url/verified_on/affiliate_url/demo:falseを登録。確認日はISO日付で30日以内。価格不明はnull。公式資料を人が確認し、記事内の数値が一致することもレビューする。

環境変数 `OPENAI_API_KEY`、`WP_URL`（HTTPS）、`WP_USER`、`WP_APP_PASSWORD` を安全に設定。GitHubに.envや値を書かない。

```bash
python -m seo_media.engine --mode live
# output内の検査結果と記事をレビュー。以下は再生成・実送信するため別の出力先を使う。
python -m seo_media.engine --mode live --post --output output/approved-run
```

現行CLIは承認済みJSONの再送信や手動承認状態の記録には未対応。実運用では生成と投稿の二段階承認を追加してから定期ライブ投稿を有効にする。WordPressへは常に下書きで送信する。ネットワーク不明時の自動リトライはしない（重複投稿回避）。投稿成功JSONを保存する。複数実行間の重複検査には同じoutputを維持する。

## CI

Actionsは既定ではモックのみ。APIキー不要。週1回のartifactを編集者が確認する。ライブへの変更はAPI予算・安全なSecrets・永続的記事履歴・人の承認フローを整えて別途レビューする。無料枠の利用条件をGitHubで確認する。

## 動作確認

Pythonテスト、モック生成、PHP lintに加え、WordPressが用意できたら320/375/768px幅でホーム・記事を確認し、下書きが一覧に公開されないこと、REST認証、比較表、リンク、キーボード操作を確認する。PHP lintだけではWordPress実動作を保証しない。
