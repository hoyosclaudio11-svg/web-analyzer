<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== BUSCANDO 'latest_posts' EN TODA LA DB ===\n\n";
global $wpdb;
$results = $wpdb->get_results("SELECT ID, post_type, post_title, post_content FROM {$wpdb->posts} WHERE post_content LIKE '%latest_posts%' AND post_status != 'trash'");
foreach ($results as $r) {
    echo "ID={$r->ID} type={$r->post_type} title={$r->post_title}\n";
    echo "  content: " . substr($r->post_content, 0, 300) . "\n\n";
}

echo "\n=== BUSCANDO EN WIDGET DATA ===\n";
$all_options = $wpdb->get_results("SELECT option_name, option_value FROM {$wpdb->options} WHERE option_name LIKE 'widget_%' AND option_value LIKE '%latest_posts%'");
foreach ($all_options as $opt) {
    echo "Option: {$opt->option_name}\n";
    echo "  " . substr($opt->option_value, 0, 500) . "\n\n";
}

echo "\n=== PRIMEROS 3 POSTS PUBLICADOS ===\n";
$recent = get_posts(["post_type"=>"post","posts_per_page"=>3,"post_status"=>"publish"]);
foreach ($recent as $p) {
    echo "  ID={$p->ID}: {$p->post_title} (date={$p->post_date})\n";
}

echo "\n=== FIN ===\n";
