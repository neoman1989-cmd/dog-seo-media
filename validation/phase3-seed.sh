#!/bin/sh
set -eu
cd /var/www/html
for slug in camera-selection camera-monthly-cost camera-recording; do
 case "$slug" in
  camera-selection) title='犬の留守番用ペットカメラの選び方：購入前に確認したい項目';;
  camera-monthly-cost) title='ペットカメラの月額費用を確認する方法：本体代と録画料金を分けて考える';;
  camera-recording) title='ペットカメラの録画を選ぶ前に：保存先・保存期間・通知を確認する';;
 esac
 id=$(wp post list --post_type=post --post_status=draft --name="$slug" --field=ID)
 if [ -z "$id" ]; then
  wp post create "/phase3/$slug.html" --post_title="$title" --post_name="$slug" --post_status=draft --quiet
 else
  wp post update "$id" "/phase3/$slug.html" --post_status=draft --quiet
 fi
done
wp post list --post_type=post --post_status=draft --fields=ID,post_name,post_status --format=json
