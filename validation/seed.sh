#!/bin/sh
set -eu
cd /var/www/html
attempt=0
until [ -f wp-config.php ]; do
 attempt=$((attempt + 1))
 [ "$attempt" -lt 30 ] || { echo "WordPress initialization timed out" >&2; exit 1; }
 sleep 2
done
if ! wp core is-installed >/dev/null 2>&1; then
  wp core install --url=http://127.0.0.1:8080 --title='犬の留守番ガイド（ローカル検証）' --admin_user=local-editor --admin_password="$LOCAL_WP_PASSWORD" --admin_email=local@example.invalid --skip-email --quiet
fi
wp theme activate dog-seo --quiet
wp option update blog_public 0 --quiet
wp option update show_on_front posts --quiet
wp option update timezone_string Asia/Tokyo --quiet
wp post delete 1 2 --force --quiet || true
page=$(wp post list --post_type=page --name=editorial-policy --field=ID)
if [ -z "$page" ]; then
 page=$(wp post create --post_type=page --post_status=publish --post_name=editorial-policy --post_title='編集方針・運営者情報' --post_content='<p>ローカル表示検証専用の固定ページです。</p><h2>編集方針</h2><p>公式情報の出典と確認日を明示します。実体験は創作せず、広告を明示します。</p>' --porcelain)
fi
post=$(wp post list --post_type=post --name=camera-comparison --field=ID)
if [ -z "$post" ]; then
 post=$(wp post create /fixtures/comparison.html --post_status=publish --post_name=camera-comparison --post_title='犬の留守番用ペットカメラの比較（検証用）' --porcelain)
fi
if ! wp menu list --fields=name --format=csv | grep -qx '検証メニュー'; then
 wp menu create '検証メニュー' --quiet
 wp menu item add-custom '検証メニュー' 'ホーム' 'http://127.0.0.1:8080' --quiet
 wp menu item add-post '検証メニュー' "$post" --quiet
 wp menu item add-post '検証メニュー' "$page" --quiet
fi
wp menu location assign '検証メニュー' primary --quiet
printf 'Local fixtures ready: comparison=%s policy=%s\n' "$post" "$page"
