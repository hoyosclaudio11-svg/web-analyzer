<?php
/**
 * River Plate Info — Correcciones Finales
 * - Arreglar contenido de Inicio (shortcode malo, tildes)
 * - Forzar limpieza total de cache
 */
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== CORRECCIONES FINALES ===\n\n";

// 1. Fix Inicio - contenido correcto
$inicio = get_page_by_path("inicio");
if ($inicio) {
    $new_content = '<!-- wp:cover {"dimRatio":50,"overlayColor":"black","minHeight":450,"align":"full","className":"river-hero"} -->
<div class="wp-block-cover alignfull river-hero" style="min-height:450px"><div class="wp-block-cover__inner-container">
<h1 class="has-text-align-center has-white-color" style="font-size:48px;font-weight:900">Bienvenido al Club Atlético River Plate</h1>
<p class="has-text-align-center has-white-color" style="font-size:20px">El Más Grande, Lejos</p>
</div></div>
<!-- /wp:cover -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Últimas Noticias</h2><!-- /wp:heading -->

<!-- wp:latest-posts {"postsToShow":6,"displayPostDate":true,"displayFeaturedImage":true,"featuredImageSizeSlug":"medium","columns":3} /-->

<!-- wp:heading {"className":"river-section-title"} --><h2>Próximo Partido</h2><!-- /wp:heading -->

<!-- wp:shortcode -->[event_list status="future" number="1"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Último Resultado</h2><!-- /wp:heading -->

<!-- wp:shortcode -->[event_results number="1"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Tabla de Posiciones</h2><!-- /wp:heading -->

<!-- wp:shortcode -->[league_table number="1"]<!-- /wp:shortcode -->';

    $result = wp_update_post(["ID" => $inicio->ID, "post_content" => $new_content], true);
    if (is_wp_error($result)) {
        echo "ERROR: " . $result->get_error_message() . "\n";
    } else {
        echo "Inicio actualizada (ID={$inicio->ID})\n";
        echo "Contenido: " . substr($new_content, 0, 100) . "...\n";
    }
}

// 2. Limpiar TODOS los caches posibles
echo "\n=== LIMPIANDO CACHES ===\n";

// WP Super Cache
if (function_exists("wp_cache_clear_cache")) {
    wp_cache_clear_cache();
    echo "WP Super Cache limpiado\n";
}
if (function_exists("prune_super_cache")) {
    prune_super_cache(true, true);
    echo "Super Cache pruneado\n";
}

// W3 Total Cache
if (function_exists("w3tc_flush_all")) {
    w3tc_flush_all();
    echo "W3 Total Cache limpiado\n";
}

// WP Rocket
if (function_exists("rocket_clean_domain")) {
    rocket_clean_domain();
    echo "WP Rocket limpiado\n";
}

// Transients
global $wpdb;
$wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '%_transient_%'");
echo "Transients limpiados\n";

// wp_cache_flush
wp_cache_flush();
echo "WP Object Cache limpiado\n";

// 3. Verificar menu
echo "\n=== MENU ===\n";
$menu = wp_get_nav_menu_object("Menu Principal");
if ($menu) {
    $items = wp_get_nav_menu_items($menu->term_id);
    foreach ($items as $item) {
        echo "  {$item->title} -> {$item->url}\n";
    }
}

echo "\n=== COMPLETADO ===\n";
