<?php
/**
 * Auditoria completa River Plate Info
 */
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";
require_once ABSPATH . "wp-admin/includes/plugin.php";

echo "=== AUDITORIA RIVER PLATE INFO ===\n\n";

// 1. TEMA ACTIVO
echo "1. TEMA\n";
$theme = wp_get_theme();
echo "   Activo: {$theme->get('Name')} (hijo de {$theme->get('Template')})\n";
echo "   Soporta custom-logo: " . (current_theme_supports("custom-logo") ? "SI" : "NO") . "\n";

// 2. LOGO
echo "\n2. LOGO\n";
$logo_id = get_theme_mod("custom_logo");
echo "   custom_logo ID: " . ($logo_id ?: "NINGUNO") . "\n";
if ($logo_id) {
    $logo_post = get_post($logo_id);
    $logo_url = wp_get_attachment_url($logo_id);
    echo "   Logo post: " . ($logo_post ? "{$logo_post->post_title} ({$logo_post->guid})" : "NO EXISTE") . "\n";
    echo "   URL: " . ($logo_url ?: "NO URL") . "\n";
    // Ver si la imagen existe en disco
    $logo_path = get_attached_file($logo_id);
    echo "   Archivo: " . ($logo_path ?: "SIN ARCHIVO") . "\n";
    if ($logo_path && file_exists($logo_path)) {
        echo "   Existe en disco: SI (" . filesize($logo_path) . " bytes)\n";
    } else {
        echo "   Existe en disco: NO\n";
    }
}
// Logo subido manualmente
$our_logo = WP_CONTENT_DIR . "/uploads/logos/river-logo.png";
echo "   Nuestro logo subido: " . (file_exists($our_logo) ? "SI (" . filesize($our_logo) . " bytes)" : "NO") . "\n";

// 3. THEME CSS
echo "\n3. CSS DEL TEMA\n";
global $wp_styles;
$theme_css = [];
foreach ($wp_styles->registered as $h => $data) {
    $src = $data->src ?? "";
    if (strpos($src, "/themes/") !== false) {
        $theme_css[] = "$h -> $src";
    }
}
echo "   Estilos de tema registrados: " . count($theme_css) . "\n";
foreach ($theme_css as $t) echo "     $t\n";

// 4. MENUS
echo "\n4. MENUS\n";
$locations = get_registered_nav_menus();
foreach ($locations as $key => $label) {
    echo "   Ubicacion: $key ($label)\n";
    $menu = wp_get_nav_menu_object(get_nav_menu_locations()[$key] ?? 0);
    if ($menu) {
        echo "     Menu: {$menu->name} (ID={$menu->term_id})\n";
        $items = wp_get_nav_menu_items($menu->term_id);
        foreach ($items as $item) {
            echo "       - {$item->title} -> {$item->url}\n";
        }
    } else {
        echo "     Sin menu asignado\n";
    }
}

// 5. PAGINAS
echo "\n5. PAGINAS\n";
$slugs = ["inicio", "plantilla", "calendario", "noticias", "tienda", "contacto"];
foreach ($slugs as $s) {
    $p = get_page_by_path($s);
    if ($p) {
        $has_shortcode = strpos($p->post_content, '[event_') !== false ||
                        strpos($p->post_content, '[player_') !== false ||
                        strpos($p->post_content, '[league_') !== false;
        echo "   /$s: ID={$p->ID}, Título={$p->post_title}, Status={$p->post_status}\n";
        echo "     Shortcodes: " . ($has_shortcode ? "SI" : "NO") . "\n";
    } else {
        echo "   /$s: NO EXISTE\n";
    }
}

// 6. SPORTSPRESS
echo "\n6. SPORTSPRESS\n";
echo "   Activo: " . (is_plugin_active("sportspress/sportspress.php") ? "SI" : "NO") . "\n";
// Contar datos de SportsPress
$player_count = wp_count_posts("sp_player")->publish ?? 0;
$event_count = wp_count_posts("sp_event")->publish ?? 0;
$team_count = wp_count_posts("sp_team")->publish ?? 0;
$table_count = wp_count_posts("sp_table")->publish ?? 0;
echo "   Jugadores: $player_count\n";
echo "   Eventos (partidos): $event_count\n";
echo "   Equipos: $team_count\n";
echo "   Tablas: $table_count\n";

// 7. FRONTPAGE
echo "\n7. PORTADA\n";
echo "   show_on_front: " . get_option("show_on_front") . "\n";
echo "   page_on_front: " . get_option("page_on_front") . "\n";
$fp = get_option("page_on_front");
if ($fp) {
    $fp_post = get_post($fp);
    echo "   Pagina: {$fp_post->post_title}\n";
    echo "   Hero presente: " . (strpos($fp_post->post_content, 'river-hero') !== false ? "SI" : "NO") . "\n";
    echo "   Shortcodes SportsPress: " . (strpos($fp_post->post_content, '[event_') !== false || strpos($fp_post->post_content, '[league_') !== false ? "SI" : "NO") . "\n";
}

// 8. CACHE
echo "\n8. CACHE\n";
$cache_plugin = "Ninguno";
if (defined("WPSC_VERSION")) $cache_plugin = "WP Super Cache v" . WPSC_VERSION;
if (defined("W3TC_VERSION")) $cache_plugin = "W3 Total Cache v" . W3TC_VERSION;
echo "   Plugin: $cache_plugin\n";
if (defined("WPSC_VERSION")) {
    echo "   Cache activo: " . ($wp_cache_enabled ?? "unknown") . "\n";
}

echo "\n=== FIN AUDITORIA ===\n";
