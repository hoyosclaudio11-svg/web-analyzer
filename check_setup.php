<?php
// Debug setup — borrar despues de usar
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== wa_river_club_setup_done: " . get_option("wa_river_club_setup_done", "NO EXISTE") . "\n\n";

echo "=== Paginas ===\n";
$slugs = ["inicio", "plantilla", "calendario", "noticias", "tienda", "contacto"];
foreach ($slugs as $s) {
    $p = get_page_by_path($s);
    echo "$s: " . ($p ? "ID={$p->ID} - {$p->post_title}" : "NO") . "\n";
}

echo "\n=== Menu ===\n";
$menu = wp_get_nav_menu_object("Menu Principal");
if ($menu) {
    echo "Menu ID: {$menu->term_id}\n";
    $items = wp_get_nav_menu_items($menu->term_id);
    if ($items) {
        foreach ($items as $item) {
            echo "  - {$item->title} (page_id={$item->object_id})\n";
        }
    }
} else {
    echo "Menu NO encontrado\n";
}

echo "\n=== Homepage ===\n";
echo "show_on_front: " . get_option("show_on_front") . "\n";
echo "page_on_front: " . get_option("page_on_front") . "\n";

echo "\n=== Logo ===\n";
$logo_id = get_theme_mod("custom_logo");
echo "custom_logo: " . ($logo_id ? $logo_id : "NO") . "\n";

echo "\n=== SportsPress ===\n";
echo "Activo: " . (is_plugin_active("sportspress/sportspress.php") ? "SI" : "NO") . "\n";
