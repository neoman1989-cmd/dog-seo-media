<!doctype html>
<html <?php language_attributes(); ?>>
<head><meta charset="<?php bloginfo('charset'); ?>"><meta name="viewport" content="width=device-width, initial-scale=1"><?php wp_head(); ?></head>
<body <?php body_class(); ?>><?php wp_body_open(); ?>
<a class="skip" href="#main">本文へ移動</a>
<header class="site-header"><div class="wrap"><a class="brand" href="<?php echo esc_url(home_url('/')); ?>">犬の留守番ガイド</a><nav aria-label="メインナビゲーション"><?php if (has_nav_menu('primary')) { wp_nav_menu(array('theme_location'=>'primary','container'=>false)); } else { ?><a href="<?php echo esc_url(home_url('/')); ?>">ホーム</a><?php } ?></nav></div></header>
