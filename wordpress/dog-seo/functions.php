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

// WordPress menus render a list; keep it horizontal and wrapping on small screens.
// Limit Japanese excerpts by characters regardless of the site's admin language.
add_filter('get_the_excerpt', function ($excerpt) {
    return wp_html_excerpt(wp_strip_all_tags($excerpt), 110, '…');
}, 20);
// Only tables scroll: the surrounding article stays readable while comparing columns.
add_filter('the_content', function ($content) {
    return preg_replace('~(<table\b[^>]*>.*?</table>)~is', '<div class="table-scroll" tabindex="0" role="region" aria-label="比較表（横にスクロールできます）">$1</div>', $content);
});
