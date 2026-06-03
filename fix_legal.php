<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== REFUERZO LEGAL — Disclaimer + Tienda + Aviso ===\n\n";

global $wpdb;

// ============================================================
// 1. CREAR / ACTUALIZAR PAGINA "AVISO LEGAL"
// ============================================================
echo "--- 1. PAGINA AVISO LEGAL ---\n";

$aviso_content = '<!-- wp:heading {"className":"river-section-title"} -->
<h2>Aviso Legal</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>River Plate Info</strong> (riverplate-info.com.ar) es un sitio de noticias e informacion <strong>INDEPENDIENTE y NO OFICIAL</strong> sobre el Club Atletico River Plate.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>1. No afiliacion</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Este sitio <strong>NO esta afiliado, respaldado, patrocinado ni aprobado</strong> por el Club Atletico River Plate, sus dirigentes, empleados o representantes. No somos el sitio oficial del club (www.cariverplate.com.ar).</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>2. Marcas y logotipos</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Las marcas, logotipos, escudos y nombres "River Plate", "CARP", "El Millonario", "La Banda" y cualquier otro signo distintivo del club son propiedad exclusiva del Club Atletico River Plate. Su uso en este sitio es meramente <strong>informativo y descriptivo</strong>, sin intencion de confundir ni aprovecharse de su reputacion.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>3. Contenido informativo</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Todo el contenido de este sitio (noticias, analisis, estadisticas) es de caracter <strong>informativo y periodistico</strong>. Las fuentes incluyen informacion publica, agencias de noticias y contenido generado por nuestro equipo. No nos hacemos responsables por errores u omisiones en los datos deportivos.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>4. Enlaces de afiliado</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>La seccion "Tienda" contiene enlaces a productos en MercadoLibre a traves de su <strong>programa de afiliados</strong>. Esto significa que podemos recibir una comision si realizas una compra a traves de dichos enlaces, sin costo adicional para vos. Los productos no son vendidos ni distribuidos por este sitio.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>5. Derechos de imagen</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Las imagenes de jugadores, partidos y estadios utilizadas en este sitio provienen de fuentes publicas y agencias de noticias. Si eres titular de derechos de alguna imagen y deseas su retirada, contactanos y sera eliminada de inmediato.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>6. Contacto</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Por cualquier consulta legal, escribinos a: <strong>contacto@riverplate-info.com.ar</strong></p>
<!-- /wp:paragraph -->

<!-- wp:separator -->
<hr class="wp-block-separator"/>
<!-- /wp:separator -->

<!-- wp:paragraph -->
<p><em>Ultima actualizacion: mayo 2026</em></p>
<!-- /wp:paragraph -->';

// Check if aviso-legal page exists
$existing = get_posts(["post_type"=>"page","name"=>"aviso-legal","posts_per_page"=>1]);
if ($existing) {
    $aviso_id = $existing[0]->ID;
    $wpdb->update($wpdb->posts, [
        "post_content" => $aviso_content,
        "post_title" => "Aviso Legal",
        "post_status" => "publish"
    ], ["ID" => $aviso_id], ["%s","%s","%s"], ["%d"]);
    echo "Aviso Legal actualizado (ID=$aviso_id)\n";
} else {
    $wpdb->insert($wpdb->posts, [
        "post_title" => "Aviso Legal",
        "post_name" => "aviso-legal",
        "post_content" => $aviso_content,
        "post_status" => "publish",
        "post_type" => "page",
        "post_date" => current_time("mysql"),
        "post_modified" => current_time("mysql"),
        "comment_status" => "closed",
        "ping_status" => "closed",
    ]);
    $aviso_id = $wpdb->insert_id;
    echo "Aviso Legal creado (ID=$aviso_id)\n";
}

// ============================================================
// 2. REFORZAR TIENDA — Afiliado claro
// ============================================================
echo "\n--- 2. REFORZANDO TIENDA ---\n";

$tienda_content = '<!-- wp:group {"className":"tienda-disclaimer-box","backgroundColor":"light-gray"} -->
<div class="wp-block-group tienda-disclaimer-box" style="background-color:#fff8e1;padding:20px;border-radius:8px;border:2px solid #ffc107;margin-bottom:24px">
<!-- wp:heading {"level":3} -->
<h3>&#9888;&#65039; Informacion importante</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Los productos que ves a continuacion son enlaces de <strong>MERCADOLIBRE AFILIADOS</strong>. Este sitio <strong>NO es la tienda oficial de River Plate</strong>. Si compras a traves de estos enlaces, podemos recibir una comision sin costo adicional para vos. La tienda oficial del club es <a href="https://www.cariverplate.com.ar" target="_blank" rel="nofollow noopener">cariverplate.com.ar</a>.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->

<!-- wp:heading {"className":"river-section-title"} -->
<h2>Camisetas de River Plate</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Encontra camisetas de River en MercadoLibre. <strong>Enlace de afiliado.</strong></p>
<!-- /wp:paragraph -->
<!-- wp:shortcode -->
[papafpro_produtos_categoria search="camiseta river plate" limit="6" columns="3"]
<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} -->
<h2>Merchandising</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Gorras, banderas y mas productos de River. <strong>Enlace de afiliado.</strong></p>
<!-- /wp:paragraph -->
<!-- wp:shortcode -->
[papafpro_produtos_categoria search="river plate merchandising gorra bandera" limit="6" columns="3"]
<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} -->
<h2>Mas Productos</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Otros productos relacionados con River Plate. <strong>Enlace de afiliado.</strong></p>
<!-- /wp:paragraph -->
<!-- wp:shortcode -->
[papafpro_produtos limit="9" columns="3"]
<!-- /wp:shortcode -->';

$wpdb->update($wpdb->posts, [
    "post_content" => $tienda_content,
    "post_title" => "Tienda"
], ["ID" => 878], ["%s","%s"], ["%d"]);
clean_post_cache(878);
echo "Tienda actualizada con aviso de afiliado y disclaimer\n";

// ============================================================
// 3. REFORZAR INICIO — Disclaimer mas visible en hero
// ============================================================
echo "\n--- 3. REFORZANDO INICIO ---\n";

$inicio_content = '<!-- wp:cover {"dimRatio":60,"overlayColor":"black","minHeight":400,"align":"full","className":"river-hero"} -->
<div class="wp-block-cover alignfull river-hero" style="min-height:400px"><div class="wp-block-cover__inner-container">
<h1 class="has-text-align-center has-white-color" style="font-size:44px;font-weight:900">River Plate Info</h1>
<p class="has-text-align-center has-white-color" style="font-size:18px">Noticias e informacion sobre el Club Atletico River Plate</p>
<p class="has-text-align-center" style="font-size:13px;color:#ffc107;margin-top:12px;font-weight:600">&#9888;&#65039; SITIO NO OFICIAL — Independiente — Creado por hinchas — No afiliado al club</p>
</div></div>
<!-- /wp:cover -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Ultimas Noticias</h2><!-- /wp:heading -->
<!-- wp:latest-posts {"postsToShow":6,"displayPostDate":true,"displayFeaturedImage":true,"featuredImageSizeSlug":"medium","columns":3} /-->

<!-- wp:heading {"className":"river-section-title"} --><h2>Proximos Partidos</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_blocks status="future" number="3"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Ultimos Resultados</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_blocks status="publish" number="3"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Tabla de Posiciones</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[league_table id="947"]<!-- /wp:shortcode -->';

$wpdb->update($wpdb->posts, [
    "post_content" => $inicio_content
], ["ID" => 866], ["%s"], ["%d"]);
clean_post_cache(866);
echo "Inicio actualizada (disclaimer destacado en amarillo en el hero)\n";

// ============================================================
// 4. AGREGAR AVISO LEGAL AL MENU (Footer menu si existe)
// ============================================================
echo "\n--- 4. AGREGANDO AL MENU ---\n";

// Add to primary menu if there's room
$menu_items = wp_get_nav_menu_items("Menu Principal");
$has_aviso = false;
if ($menu_items) {
    foreach ($menu_items as $item) {
        if (strpos($item->url, "aviso-legal") !== false) $has_aviso = true;
    }
}

if (!$has_aviso && $menu_items) {
    // Get the menu ID
    $menu_locations = get_nav_menu_locations();
    $menu_id = isset($menu_locations["primary"]) ? $menu_locations["primary"] : 0;
    if (!$menu_id) {
        // Try to find by name
        $menus = wp_get_nav_menus();
        foreach ($menus as $m) {
            if ($m->name === "Menu Principal") $menu_id = $m->term_id;
        }
    }
    if ($menu_id) {
        wp_update_nav_menu_item($menu_id, 0, [
            "menu-item-title" => "Aviso Legal",
            "menu-item-url" => "/aviso-legal",
            "menu-item-status" => "publish",
            "menu-item-type" => "custom",
            "menu-item-attr-title" => "Aviso Legal — Sitio NO Oficial",
        ]);
        echo "Item Aviso Legal agregado al Menu Principal\n";
    }
} else {
    echo "Aviso Legal ya existe en el menu o no hay menu principal\n";
}

// ============================================================
// 5. AGREGAR WIDGET DE DISCLAIMER EN FOOTER
// ============================================================
echo "\n--- 5. WIDGET DISCLAIMER FOOTER ---\n";

// Update or create a text widget with disclaimer in footer sidebar
$sidebars = get_option("sidebars_widgets", []);
$footer_key = null;
foreach ($sidebars as $key => $widgets) {
    if (strpos($key, "footer") !== false && is_array($widgets)) {
        $footer_key = $key;
        break;
    }
}

if ($footer_key) {
    echo "Footer sidebar encontrada: $footer_key\n";
    // Get existing text widgets
    $text_widgets = get_option("widget_text", []);
    $found = false;
    foreach ($text_widgets as $idx => $w) {
        if (is_array($w) && isset($w["title"]) && strpos($w["title"], "Aviso") !== false) {
            echo "Widget de aviso ya existe en text widgets (idx=$idx)\n";
            $found = true;
            break;
        }
    }
    if (!$found) {
        // Add new text widget
        $new_idx = max(array_keys($text_widgets)) + 1;
        $text_widgets[$new_idx] = [
            "title" => "Aviso Legal",
            "text" => '<p style="font-size:11px;color:#888;text-align:center">&#9888;&#65039; <strong>SITIO NO OFICIAL.</strong> Independiente y sin vinculo con el Club Atletico River Plate. Las marcas y logotipos pertenecen a sus respectivos titulares. Enlaces a MercadoLibre son de afiliado. <a href="/aviso-legal">Mas info</a>.</p>',
            "filter" => false,
            "visual" => false,
        ];
        update_option("widget_text", $text_widgets);

        // Add to footer sidebar
        $sidebars[$footer_key][] = "text-$new_idx";
        update_option("sidebars_widgets", $sidebars);
        echo "Widget disclaimer agregado al footer (text-$new_idx)\n";
    }
} else {
    echo "No se encontro sidebar de footer, creando opcion alternativa...\n";
    // Create the widget option anyway so it's available
    $text_widgets = get_option("widget_text", []);
    $new_idx = max(array_keys($text_widgets)) + 1;
    $text_widgets[$new_idx] = [
        "title" => "Aviso Legal",
        "text" => '<p style="font-size:11px;color:#888;text-align:center">&#9888;&#65039; <strong>SITIO NO OFICIAL.</strong> Independiente y sin vinculo con el Club Atletico River Plate. Las marcas y logotipos pertenecen a sus respectivos titulares. Enlaces a MercadoLibre son de afiliado. <a href="/aviso-legal">Mas info</a>.</p>',
        "filter" => false,
        "visual" => false,
    ];
    update_option("widget_text", $text_widgets);
    echo "Widget text creado (no asignado a sidebar, disponible manualmente)\n";
}

// ============================================================
// 6. VERIFICACION FINAL
// ============================================================
echo "\n--- 6. VERIFICACION ---\n";
echo "Aviso Legal page: " . (get_post($aviso_id) ? "OK (ID=$aviso_id)" : "ERROR") . "\n";
echo "Tienda title: " . get_post(878)->post_title . "\n";
echo "Tienda tiene 'NO es la tienda oficial': " . (strpos(get_post(878)->post_content, "NO es la tienda oficial") !== false ? "SI" : "NO") . "\n";
echo "Inicio tiene 'SITIO NO OFICIAL': " . (strpos(get_post(866)->post_content, "SITIO NO OFICIAL") !== false ? "SI" : "NO") . "\n";

echo "\n=== COMPLETADO ===\n";
