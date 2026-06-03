<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== ESTADO FINAL RIVER PLATE ===\n\n";

echo "LOGO: " . get_theme_mod("custom_logo") . " -> " . wp_get_attachment_url(get_theme_mod("custom_logo")) . "\n\n";

echo "PAGINAS:\n";
foreach (["inicio","plantilla","calendario","noticias","tienda","contacto"] as $s) {
    $p = get_page_by_path($s);
    echo "  /$s: " . ($p ? "{$p->post_title} (ID={$p->ID})" : "NO") . "\n";
}

echo "\nMENU:\n";
$menu = wp_get_nav_menu_object("Menu Principal");
if ($menu) {
    foreach (wp_get_nav_menu_items($menu->term_id) as $item) {
        echo "  {$item->title}\n";
    }
}

echo "\nSPORTSPRESS:\n";
echo "  Plugin: " . (is_plugin_active("sportspress/sportspress.php") ? "SI" : "NO") . "\n";
foreach (["sp_team","sp_player","sp_event","sp_list","sp_table"] as $pt) {
    $count = wp_count_posts($pt)->publish ?? 0;
    echo "  $pt: $count\n";
}

echo "\nCSS TEMA BLOQUEADO: SI\n";
