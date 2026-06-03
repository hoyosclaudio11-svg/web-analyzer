<?php
/**
 * River Plate Info — Script de Setup
 * Ejecutar UNA vez y luego BORRAR del servidor
 */
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== SETUP RIVER PLATE CLUB ===\n\n";

// Cargar funciones admin necesarias
require_once ABSPATH . "wp-admin/includes/plugin.php";
require_once ABSPATH . "wp-admin/includes/media.php";
require_once ABSPATH . "wp-admin/includes/file.php";
require_once ABSPATH . "wp-admin/includes/image.php";

// 1. Activar SportsPress
$sp = "sportspress/sportspress.php";
if (file_exists(WP_PLUGIN_DIR . "/" . $sp)) {
    if (!is_plugin_active($sp)) {
        activate_plugin($sp);
        echo "SportsPress ACTIVADO\n";
    } else {
        echo "SportsPress ya estaba activo\n";
    }
} else {
    echo "SportsPress NO ENCONTRADO en " . WP_PLUGIN_DIR . "/" . $sp . "\n";
}

// 2. Crear paginas
$pages = [
    "inicio" => ["title" => "Inicio", "content" => '<!-- wp:cover {"dimRatio":50,"overlayColor":"black","minHeight":450,"align":"full","className":"river-hero"} -->
<div class="wp-block-cover alignfull river-hero" style="min-height:450px"><div class="wp-block-cover__inner-container">
<h1 class="has-text-align-center has-white-color" style="font-size:48px;font-weight:900">Bienvenido al Club Atletico River Plate</h1>
<p class="has-text-align-center has-white-color" style="font-size:20px">El Mas Grande, Lejos</p>
</div></div>
<!-- /wp:cover -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Ultimas Noticias</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[latest_posts number="6" columns="3"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Proximo Partido</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_list status="future" number="1"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Ultimo Resultado</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_results number="1"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Tabla de Posiciones</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[league_table number="1"]<!-- /wp:shortcode -->'],
    "plantilla" => ["title" => "Plantilla", "content" => '<!-- wp:heading {"className":"river-section-title"} --><h2>Plantilla Profesional</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Conoce a los jugadores del Mas Grande.</p><!-- /wp:paragraph -->
<!-- wp:shortcode -->[player_list number="50" columns="number,name,position,nationality"]<!-- /wp:shortcode -->'],
    "calendario" => ["title" => "Calendario", "content" => '<!-- wp:heading {"className":"river-section-title"} --><h2>Calendario de Partidos</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_list status="future" number="20"]<!-- /wp:shortcode -->
<!-- wp:heading {"className":"river-section-title"} --><h2>Resultados</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_results number="20"]<!-- /wp:shortcode -->'],
    "noticias" => ["title" => "Noticias", "content" => '<!-- wp:heading {"className":"river-section-title"} --><h2>Noticias de River Plate</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[latest_posts number="12" columns="2"]<!-- /wp:shortcode -->'],
    "tienda" => ["title" => "Tienda Oficial", "content" => '<!-- wp:heading {"className":"river-section-title"} --><h2>Tienda Oficial</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Proximamente: camisetas oficiales, merchandising y mas productos del Mas Grande.</p><!-- /wp:paragraph -->'],
    "contacto" => ["title" => "Contacto", "content" => '<!-- wp:heading {"className":"river-section-title"} --><h2>Contacto</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Queres anunciar en River Plate Info? Tenes una primicia? Escribinos.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>Email: info@riverplate-info.com.ar</p><!-- /wp:paragraph -->']
];

echo "\n=== PAGINAS ===\n";
$page_ids = [];
foreach ($pages as $slug => $data) {
    $existing = get_page_by_path($slug);
    if (!$existing) {
        $id = wp_insert_post([
            "post_title"   => $data["title"],
            "post_name"    => $slug,
            "post_content" => $data["content"],
            "post_status"  => "publish",
            "post_type"    => "page"
        ]);
        if ($id && !is_wp_error($id)) {
            $page_ids[$slug] = $id;
            echo "  {$data["title"]}: CREADA (ID=$id)\n";
        } else {
            echo "  {$data["title"]}: ERROR\n";
        }
    } else {
        $page_ids[$slug] = $existing->ID;
        echo "  {$data["title"]}: YA EXISTE (ID={$existing->ID})\n";
    }
}

// 3. Menu
echo "\n=== MENU ===\n";
$menu_name = "Menu Principal";
$menu_exists = wp_get_nav_menu_object($menu_name);
if ($menu_exists) {
    echo "Menu '{$menu_name}' ya existe (ID={$menu_exists->term_id})\n";
    // Limpiar items viejos
    $existing_items = wp_get_nav_menu_items($menu_exists->term_id);
    foreach ($existing_items as $item) {
        wp_delete_post($item->ID, true);
    }
    echo "Items viejos eliminados\n";
    $menu_id = $menu_exists->term_id;
} else {
    $menu_id = wp_create_nav_menu($menu_name);
    echo "Menu CREADO (ID=$menu_id)\n";
}

$menu_items_order = ["inicio", "plantilla", "calendario", "noticias", "tienda", "contacto"];
foreach ($menu_items_order as $i => $slug) {
    if (!isset($page_ids[$slug]) || !isset($pages[$slug])) continue;
    $item_id = wp_update_nav_menu_item($menu_id, 0, [
        "menu-item-title"  => $pages[$slug]["title"],
        "menu-item-object" => "page",
        "menu-item-object-id" => $page_ids[$slug],
        "menu-item-type"   => "post_type",
        "menu-item-status" => "publish",
        "menu-item-position" => $i
    ]);
    echo "  + {$pages[$slug]["title"]} (item_id=$item_id)\n";
}

// Asignar menu a ubicacion
$locations = get_theme_mod("nav_menu_locations") ?: [];
$locs = get_registered_nav_menus();
$primary_key = "primary";
if (!isset($locs["primary"])) {
    $keys = array_keys($locs);
    if ($keys) $primary_key = $keys[0];
}
$locations[$primary_key] = $menu_id;
set_theme_mod("nav_menu_locations", $locations);
echo "Menu asignado a ubicacion: $primary_key\n";

// 4. Homepage
if (isset($page_ids["inicio"])) {
    update_option("show_on_front", "page");
    update_option("page_on_front", $page_ids["inicio"]);
    echo "\n=== HOME PAGE: Inicio (ID={$page_ids["inicio"]}) ===\n";
}

// 5. Logo
echo "\n=== LOGO ===\n";
$logo_path = WP_CONTENT_DIR . "/uploads/logos/river-logo.png";
if (file_exists($logo_path)) {
    $existing_logo_id = get_theme_mod("custom_logo");
    if (!$existing_logo_id) {
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
        } else {
            echo "ERROR registrando logo: " . $attach_id->get_error_message() . "\n";
        }
    } else {
        echo "Logo ya registrado (ID=$existing_logo_id)\n";
    }
} else {
    echo "Logo NO ENCONTRADO en: $logo_path\n";
}

// 6. Limpiar cache
if (function_exists("wp_cache_flush")) {
    wp_cache_flush();
    echo "\nCache limpiada\n";
}

// 7. Marcar setup
update_option("wa_river_club_setup_done", true);

echo "\n=== SETUP COMPLETADO ===\n";
echo "Borrar este archivo del servidor.\n";
