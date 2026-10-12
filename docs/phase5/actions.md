# GitHub Actionsの稼働確認

2026-10-12の `gh api repos/neoman1989-cmd/dog-seo-media/actions/runs` はForbidden。Gitの読み書き成功はAPIやActionsの稼働を証明しない。リモートジョブは起動していない。

現在の指示は外部アカウント作成・課金禁止。既存オーナーのGitHub画面での確認操作を以下に整理する。アカウントを新しく作ったり、APIトークン値をチャット/Gitへ保存したりしない。

1. リポジトリ→Actions→Draft editorial pipelineの最近のrunを開き、ブランチ/日時/commit/statusを記録する。
2. Settings→Actions→GeneralでActions許可とWorkflow permissionsを確認。モック状態保存にはcontents:write、週次分析モックはcontents:readを使用する。
3. editorial-stateが保持され、削除/force pushされていないかを確認。保護ルールが通常のCI pushを妨げる場合はオーナーが必要な範囲だけ調整する。
4. 既存runのTests/Restore durable ledger/Generate mockのログを読む。snapshotのversion、API予約0、投稿0、承認なしを確認。
5. 初回と次のrunを比較し、同一語はAlready generated; skipped、状態ブランチの保存と復元が成功したことを確認する。artifactが空でも再生成スキップならそれ自体は異常でない。
6. 手動Run workflowはGitHub無料枠/課金設定とオーナーの実行許可を確認した後だけ。今回Codexは実行しない。mainが選択され、Secrets不要のmockであることを確認する。
7. ログと実際のbranch保存を見た後でのみ稼働確認済みとする。Forbiddenや未取得を成功として報告しない。

ローカルのPython77テストと一時Gitリモートの既存モック保存/復元テストは成功したが、GitHub-hosted実行・GITHUB_TOKENの権限・無料枠の実稼働は未確認。Phase 5の追加モジュールはネットワークなしで試算と判断を再生成できる。
