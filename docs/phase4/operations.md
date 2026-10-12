# 接続、週次運用、リンク切替、Actions

## Google Search Console（オーナーの所有権確認後）

1. 本番ドメインが決まってからプロパティを作成。DomainプロパティならGoogle提示のDNS TXTをオーナーが追加。DNS・所有権変更は許可なしで実行しない。
2. HTTPS・canonical・検索ブロック解除の判断・サイトマップを確認。WordPress標準のwp-sitemap.xmlを検証して送信。未公開ステージングを送信しない。
3. 最初は無料の画面CSVエクスポートを利用。期間を7日間、ページ単位で揃え、同じページの重複・クエリ付きURLを排除。読み取りAPIは将来webmasters.readonlyで接続し、OAuth更新トークンはSecure environmentに保存する。
4. 正規化CSVの列はpage,clicks,impressions,position。日本語の管理画面列名はこの名前に変換する。CTRは同じ期間・ページのクリック/表示から計算し、0表示なら未計算。

## GA4（タグは未設置）

1. オーナーがプロパティとWebストリームを作成し、プライバシー/同意管理を確認する。新規サービス登録は許可後のみ。
2. 本番の測定IDを設定。プラグイン・GTM・テーマ埋込を重複させない。Cookie同意前の挙動、DebugView、イベント二重発火を検証する。
3. localhost/preview/wp-admin/内部アクセスを除外。メール・氏名・IP・クエリ文字列を独自イベントへ送らない。
4. official_outbound_clickとaffiliate_outbound_clickを別イベントにする。普通の公式リンククリックは広告収益ではない。実成果はASP承認レポートと照合する。現在のHTMLにはdata-link-typeがあり、将来のイベント分類に使える。タグ送信コードはまだ設置しない。
5. APIを利用するならanalytics.readonly、秘密情報は環境設定へ。Google公式の無料範囲とクォータを確認し、有料BigQuery等は勝手に追加しない。

## 週次分析

```bash
python -m seo_media.weekly --mock
python -m seo_media.weekly --current /secure/current.csv --previous /secure/previous.csv --site-host your-domain.example --output output/weekly.json
```

モックはsynthetic_fixtureと明示し、実トラフィックとして扱わない。入力は週・ページ単位の集約CSV。重複ページ、別ホスト、不正指標を拒否。平均掲載順位8〜20かつ表示100以上は検索意図と内部リンクの手動レビュー候補、100未満はデータ不足。しきい値は編集方針でありGoogleの推奨基準ではない。

毎週、検索クリック/CTR/平均掲載順位、送客、ASP承認成果、実費を確認。記事数を増やす前に、案件単価が確認できたか、購入可能か、読者の疑問に答えたかを確認する。推奨レポートから自動リライト・投稿・公開は行わない。生データはGitに入れずoutput/か安全な保管場所へ。GA4の実レポート自動取得は未実装。

## 公式リンクから広告リンクへの切替

既定は通常公式リンク。config/monetization.example.jsonはaffiliate_enabled:false。広告無効・未承認・期限切れ・URL改変・別商品・不明ドメインなら公式へfallbackする。

将来オーナーの許可とASP承認を得た後のみ、ASPが提供した実URLをaffiliateレコードに保存する。必須はstatus:approved、product_id、ASP、承認ID、approved_on、expires_on、url、owner_reviewer、owner_approval_hash。許可ホストはASPの文書と提供URLから確認する。ハッシュは承認済みレコードの誤変更検知であり、ASP承認の真偽を暗号的に証明する署名ではない。真偽・期限・転載条件はオーナーが確認する。

オーナーがconfig/monetization.json（Git除外）のaffiliate_enabledを真のboolean trueにして明示したホストだけを許可する。レンダラーは広告表示、sponsored/nofollow、link_typeを付与。出典リンクは通常の公式URLのまま。記事HTMLが変わるので生成し直し、品質・ハッシュ承認を再実行する。旧承認のまま投稿しない。切替テストのexample.com URLはテスト専用で、実台帳には一切設定していない。

## GitHub Actionsの確認操作

今回の `gh api .../actions/runs` はForbidden。Git読み書きの成功はGitHub API権限やActions成功を意味しない。Codexからリモートジョブは起動していない。

オーナーはGitHub→このリポジトリ→Actions→Draft editorial pipelineで最近のrunとjobログを確認。Settings→Actions→GeneralでActions許可とWorkflow permissionsを確認する。状態保存ジョブにはcontents:writeが必要。editorial-stateブランチの保護がCIの通常pushを妨げないかを確認し、force push/削除は禁止する。

無料枠・課金設定を確認してからworkflow_dispatchのRun workflowでmainを指定。Tests→Restore durable ledger→Generate mock articlesの成功、editorial-stateのledger.json、API予約0・投稿0・承認なしを確認。2回目に同じキーワードがAlready generated; skippedとなることを確認する。初回と2回目のログを保存し、成功を見た後でのみ稼働確認済みとする。

追加のWeekly analysis smoke testは手動起動のみ、contents:read、無料モックデータ。まだGitHub上で実行していない。ローカルの同等モック・状態テストは実行済み。APIトークン値はチャットへ送らず、必要ならGitHub接続を権限範囲に応じて設定する。
