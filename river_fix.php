<?php
/**
 * River Plate Info — Correcciones
 * Arregla: contenido de paginas, menu, logo
 */
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";
require_once ABSPATH . "wp-admin/includes/plugin.php";
require_once ABSPATH . "wp-admin/includes/media.php";
require_once ABSPATH . "wp-admin/includes/file.php";
require_once ABSPATH . "wp-admin/includes/image.php";

echo "=== CORRECCIONES RIVER PLATE ===\n\n";

// 1. Corregir pagina Inicio (typos + contenido mejorado)
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
    wp_update_post(["ID" => $inicio->ID, "post_content" => $new_content]);
    echo "Pagina Inicio (ID={$inicio->ID}) actualizada con tildes correctas\n";
} else {
    echo "ERROR: Inicio no encontrada\n";
}

// 2. Recrear menu limpio
echo "\n=== MENU ===\n";
$menu_name = "Menu Principal";
$menu_exists = wp_get_nav_menu_object($menu_name);

if ($menu_exists) {
    // Borrar menu viejo completamente
    wp_delete_nav_menu($menu_name);
    echo "Menu viejo eliminado\n";
}

// Crear menu nuevo
$menu_id = wp_create_nav_menu($menu_name);
echo "Menu nuevo creado (ID=$menu_id)\n";

// Paginas en orden
$slugs = ["inicio", "plantilla", "calendario", "noticias", "tienda", "contacto"];
$titles = ["Inicio", "Plantilla", "Calendario", "Noticias", "Tienda Oficial", "Contacto"];

foreach ($slugs as $i => $slug) {
    $page = get_page_by_path($slug);
    if ($page) {
        $item_id = wp_update_nav_menu_item($menu_id, 0, [
            "menu-item-title"  => $titles[$i],
            "menu-item-object" => "page",
            "menu-item-object-id" => $page->ID,
            "menu-item-type"   => "post_type",
            "menu-item-status" => "publish",
            "menu-item-position" => $i
        ]);
        if ($item_id && !is_wp_error($item_id)) {
            echo "  + {$titles[$i]} (item_id=$item_id, page_id={$page->ID})\n";
        } else {
            echo "  ERROR: {$titles[$i]} - " . (is_wp_error($item_id) ? $item_id->get_error_message() : "unknown") . "\n";
        }
    } else {
        echo "  FALTA pagina: $slug\n";
    }
}

// Asignar a ubicacion del tema
$locations = get_theme_mod("nav_menu_locations") ?: [];
$locs = get_registered_nav_menus();
echo "\nUbicaciones de menu disponibles:\n";
foreach ($locs as $key => $label) {
    echo "  $key => $label\n";
}
$primary_key = "primary";
if (!isset($locs["primary"])) {
    $keys = array_keys($locs);
    if ($keys) $primary_key = $keys[0];
}
$locations[$primary_key] = $menu_id;
set_theme_mod("nav_menu_locations", $locations);
echo "Menu asignado a: $primary_key\n";

// 3. Asegurar logo
echo "\n=== LOGO ===\n";
$logo_path = WP_CONTENT_DIR . "/uploads/logos/river-logo.png";
if (file_exists($logo_path)) {
    $logo_id = get_theme_mod("custom_logo");
    if ($logo_id) {
        echo "Logo ya registrado (ID=$logo_id). Verificando tema...\n";
        // Forzar soporte custom-logo en el tema
        add_theme_support("custom-logo", [
            "height" => 120,
            "width" => 120,
            "flex-height" => true,
            "flex-width" => true
        ]);
    } else {
        // Registrar de nuevo
        $attach_id = wp_insert_attachment([
            "guid"           => content_url("/uploads/logos/river-logo.png"),
            "post_mime_type" => "image/png",
            "post_title"     => "River Plate Logo",
            "post_status"    => "inherit"
        ], $logo_path);
        if (!is_wp_error($attach_id)) {
            $meta = wp_generate_attachment_metadata($attach_id, $logo_path);
            wp_update_attachment_metadata($attach_id, $meta);
            set_theme_mod("custom_logo", $attach_id);
            echo "Logo registrado (ID=$attach_id)\n";
        }
    }
}

// 4. Verificar SportsPress
echo "\n=== SPORTSPRESS ===\n";
echo "Activo: " . (is_plugin_active("sportspress/sportspress.php") ? "SI" : "NO") . "\n";

// 5. Limpiar cache
if (function_exists("wp_cache_flush")) {
    wp_cache_flush();
    echo "\nCache limpiada.\n";
}

echo "\n=== CORRECCIONES COMPLETADAS ===\n";
