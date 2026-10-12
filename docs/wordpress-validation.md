# WordPressローカル検証

2026-10-12 JST、mainの1661544から `feat/wordpress-validation` を作成して検証。

## 再現手順

Docker Engine + Compose、Python 3.11+、Node 24、Chromiumと日本語フォントを用意する。プロジェクトルートから実行。

```bash
python validation/init.py
# 既存のvalidation/.envがあれば再生成不要。パスワードはローカルランダム生成、Git追跡しない。
docker compose --project-name dog-media-validation --env-file validation/.env -f validation/compose.yml up -d wordpress
docker compose --project-name dog-media-validation --env-file validation/.env -f validation/compose.yml run --rm cli
cd validation/browser
npm ci
npm test
```

既存のChromiumを `/usr/bin/chromium` として使用。別の場所なら `CHROMIUM_PATH=/path/to/chromium npm test`。Playwright同梱ブラウザなら `npx playwright install --with-deps chromium` の後 `CHROMIUM_PATH=bundled npm test`。クラウドではダウンロード先がネットワーク制限で403だったため、インストール済みChromiumを使用した。

サイトへの接続は内部検証用途のみ。localhostをユーザー向けプレビューとして公開しない。Dockerは127.0.0.1:8080だけにポートをbindし、dbに外部ポートはない。internalネットワーク、WordPressの外部HTTP遮断、自動更新・cron無効により実行中の外部サービス接続を防ぐ。Dockerイメージ・npmパッケージ取得はセットアップ時に必要。

このクラウドではDockerと実行シェルのネットワーク名前空間が異なり、ホストへの公開ポートがシェル側で利用できなかった。直接到達できるWordPressコンテナIPを `docker inspect dog-media-validation-wordpress-1 --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'` で確認し、`python validation/forward.py <container-ip>` を別ターミナルで実行してループバックだけに転送した。通常のDocker環境では不要。コンテナ再作成時にIPを再確認する。

seedはローカル専用の比較記事と固定ページを作り、画面検証のためローカルDB内で公開状態にする。本番WordPressや外部APIには投稿しない。架空の比較テンプレートは実商品記事ではない。テーマはread-only mount。サンプル投稿の削除とメニュー作成はこの専用DBだけに適用。seed再実行後もfixtureは増えないことを確認。

終了はプロジェクトルートで同じCompose引数を指定して `down`。DBは名前付きvolumeで保持。検証データを消す場合に限り `down -v`。秘密情報のvalidation/.envは削除せず、再起動時に再利用する。

## 実行結果

|対象|結果|
|---|---|
|WordPress 6.8.3 / PHP 8.3、MariaDB 11.4|起動・テーマ有効化成功|
|トップ・比較記事・固定ページ × 320/375/768/1280px|Playwright 12件成功|
|各ページHTTP・h1・ナビ・フッター・ページ全体横はみ出し|全幅で正常|
|新着記事リンク、110文字以下の日本語抜粋|成功|
|比較表、広告表示、モバイル横スクロール、キーボード操作|成功|
|JavaScript pageerror|0件|
|PHP構文検査|7ファイル成功|
|Pythonテスト|33件成功|

スクリーンショットは `artifacts/wordpress/` に12枚、修正前比較2枚も保存。結果JSONは同ディレクトリのbrowser-results.json。Chromiumの画面幅検証であり、実機iOS Safari・Androidや全ブラウザを検証したものではない。

## 表示修正

- WordPressメニューのulにflex・折り返し・箇条書き除去を適用。
- 日本語抜粋を110文字へ制限（管理画面の言語が英語でも極端に長くしない）。
- 記事全体の横スクロールを廃止し、表だけにスクロール可能・キーボードfocus可能な領域を作成。
- モバイル記事見出しの文字サイズと行間を調整。

## Actionsと状態保存

既存editorial.ymlの実コマンドを、一時ローカルbare Gitリモートと2つの新規cloneで実行した。最初の実行でmock記事と台帳を保存し、別runnerで復元して2回目は生成をスキップ。API予約0、投稿0、承認0を確認。Git保存競合・破損・取得失敗などの既存テストも成功。

GitHub APIのActions結果取得はForbiddenで拒否され、実際のGitHub-hosted runやGITHUB_TOKENの書込み権限は未確認。リモートのeditorial-stateブランチも確認時点では存在しなかった。これをActions成功の証拠とは扱わない。

追加のwordpress-validation.ymlは手動実行専用、contents:read、APIキー不要。ローカルWordPressとブラウザ検証後にartifactを保存し、alwaysで停止する。今回リモートでのActions実行はしない。GitHubで実行する場合は無料枠・課金設定を先に確認する。モックeditorial.ymlの定期スケジュールは変更していない。
