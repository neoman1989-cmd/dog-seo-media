<?php
if (!defined('ABSPATH')) { exit; }
add_action('after_setup_theme', function () {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', array('search-form', 'comment-form', 'gallery', 'caption', 'style', 'script'));
    register_nav_menus(array('primary' => 'メインナビゲーション'));
});
add_action('wp_enqueue_scripts', function () {
    wp_enqueue_style('dog-seo', get_stylesheet_uri(), array(), '0.1.0');
});
