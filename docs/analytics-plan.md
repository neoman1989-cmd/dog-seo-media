# Search Console / GA4 接続設計（未接続）

解析・本番公開は未実施。config/analytics.example.jsonはenabled:false。WordPressにトラッキングタグを追加していない。認証値はリポジトリへ保存しない。

## Search Console

本番サイトの所有権確認後に、読み取り専用スコープwebmasters.readonlyを使う。まず無料のCSVエクスポートを利用し、有料順位APIは使わない。日別・正規ページURL別のclicks/impressions/positionを取得し、記事IDと対応させる。Search ConsoleのCTRを計算する場合は同じ集計範囲のclicks/impressionsから算出し、impressions=0なら未計算。平均掲載順位を正確な固定順位として解釈しない。

seo_media.analytics.import_search_consoleはネットワークなしの正規化CSV入力に対応。列はpage,clicks,impressions,position。入力URLは本番ホストのHTTPSのみ、クエリ付きURLを拒否。これはGoogleへのAPI接続ではなく、ローカルの取得データ処理基盤。

週次で8〜20位などの改善候補をレビュー用レポートに出す計画。期間差・季節差・クリック数を考慮し、データ不足なら結論を出さない。リライトは別下書きと差分レビューを作り、自動公開しない。検索語別データは個人情報を含み得るので、公開台帳・Gitには保存せず、保持期間を限定する。

## GA4

本番ドメインとプライバシーポリシー、同意管理を整えた後にプロパティを設定。measurement_idは公開可能な識別子だが、OAuth token・サービスアカウント鍵はSecure environmentへ保存。Data APIはanalytics.readonly。検証環境、管理画面、preview URLは計測しない。

予定イベントはpage_viewとofficial_outbound_click。記事IDとlink_type:officialを付け、ユーザーの入力、メール、IP、クエリ文字列をイベント値に含めない。現段階の通常リンククリックをアフィリエイト成果と呼ばない。ASP承認後にaffiliate_outbound_clickを別イベントとして追加するが、実承認成果はASPの承認レポートで照合する。

KPIは検索クリック、読者が必要情報に到達した割合、公式リンク送客、将来の承認済み成果、実費。未計測の成約率や収益を作らない。GA4 / Search Console連携には所有権・API権限・同意管理の確認が必要で、今回の稼働済み機能とは扱わない。
