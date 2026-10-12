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

記事生成と投稿は別コマンドです。今回の作業ではライブは禁止です。APIキーを入れずに以下のモック手順を試せます。

```bash
python -m seo_media.engine init-state
python -m seo_media.engine generate --mode mock
# output/article-<hash>.jsonを編集者が確認。実際のパスを指定する。
python -m seo_media.engine approve --article output/article-<hash>.json
python -m seo_media.engine post --mode mock --article output/article-<hash>.json
```

approveは生成台帳に登録されたJSONのSHA-256を記録します。投稿は同じハッシュと現在の品質ゲートの成功が必須です。承認後の内容変更は拒否します。空白やJSONキー順はハッシュに影響しません。JSON内容の編集を伴うリライトの登録フローは未対応です。

将来ライブを明示的に許可する場合のみ、確認済み予算設定と専用状態ブランチを利用します。予算・障害時の復旧仕様は [safety.md](safety.md) を先に確認してください。生成と投稿のCLIはそれぞれ `generate --mode live --budget-config <file> --state-git-dir <repo-root>` と `post --mode live --article <file> --state-git-dir <repo-root>` です。生成から投稿への自動連携はありません。承認も同じ永続台帳に `approve --state-git-dir <repo-root>` で保存します。

## CI

Actionsはモック生成のみ。キー不要で、承認・投稿コマンドは実行しません。日曜23:00 UTC（月曜08:00 JST）、および手動起動。スケジュールはデフォルトブランチへマージ後に有効になります。

履歴保存のためGITHUB_TOKENのcontents:writeを専用 `editorial-state` ブランチへのpushに使用します。状態取得・保存が失敗すると生成を停止。リポジトリ設定でActionsの書込みが許可されている必要があります。Artifactはレビュー用で、重複判定の保存元には使いません。キャッシュの欠落や14日のartifact期限によって履歴を失いません。

## 動作確認

Pythonテスト、モック生成、PHP lintに加え、WordPressが用意できたら320/375/768px幅でホーム・記事を確認し、下書きが一覧に公開されないこと、REST認証、比較表、リンク、キーボード操作を確認する。PHP lintだけではWordPress実動作を保証しない。
