<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== FIX HOMEPAGE + REVERTIR PATCH ===\n\n";

// 1. Revertir el patch de SportsPress
$file = WP_PLUGIN_DIR . "/sportspress/includes/sp-core-functions.php";
$backup = $file . ".bak_20260515";
if (file_exists($backup)) {
    copy($backup, $file);
    unlink($backup);
    echo "1. Patch de SportsPress REVERTIDO (restaurado backup)\n";
} else {
    echo "1. No hay backup para revertir\n";
}

// 2. Actualizar Inicio - solo shortcodes que funcionan (sin publish events)
echo "\n2. Actualizando Inicio (sin event_blocks publish)...\n";

global $wpdb;

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
<!-- wp:shortcode -->[event_blocks status="future" number="5"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Tabla de Posiciones</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[league_table id="947"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Plantel Profesional</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[player_list id="944" limit="12"]<!-- /wp:shortcode -->';

$wpdb->update($wpdb->posts, ["post_content" => $inicio_content], ["ID" => 866], ["%s"], ["%d"]);
clean_post_cache(866);
echo "   Inicio actualizada: sin event_blocks publish, con player_list y mas future events\n";

// 3. Arreglar pagina Calendario (ID=876) si tiene shortcodes problematicos
echo "\n3. Revisando Calendario...\n";
$cal = get_post(876);
if ($cal) {
    $cal_content = $cal->post_content;
    if (strpos($cal_content, 'status="publish"') !== false || strpos($cal_content, "status='publish'") !== false) {
        echo "   Calendario tiene shortcodes problematicos\n";
        // Reemplazar event_blocks con status=publish por solo future
        $new_cal = '<!-- wp:heading {"className":"river-section-title"} --><h2>Calendario de Partidos</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_blocks status="future" number="10"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Tabla de Posiciones</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[league_table id="947"]<!-- /wp:shortcode -->';
        $wpdb->update($wpdb->posts, ["post_content" => $new_cal], ["ID" => 876], ["%s"], ["%d"]);
        clean_post_cache(876);
        echo "   Calendario actualizado (sin event_blocks publish)\n";
    } else {
        echo "   Calendario OK, sin shortcodes problematicos\n";
    }
}

// 4. Verificar pagina Noticias (ID=875)
echo "\n4. Revisando Noticias...\n";
$noti = get_post(875);
if ($noti) {
    $noti_content = $noti->post_content;
    if (strpos($noti_content, "event_blocks") !== false || strpos($noti_content, "event_list") !== false) {
        echo "   Noticias tiene shortcodes de eventos - verificando...\n";
    } else {
        echo "   Noticias OK\n";
    }
}

// 5. Verificar que la homepage funciona
echo "\n5. Probando homepage...\n";
$response = wp_remote_get("https://riverplate-info.com.ar/", ["timeout" => 30, "sslverify" => false]);
if (is_wp_error($response)) {
    echo "   ERROR: " . $response->get_error_message() . "\n";
} else {
    $code = wp_remote_retrieve_response_code($response);
    echo "   Status: $code\n";
    if ($code == 200) {
        echo "   HOMEPAGE FUNCIONANDO!\n";
    }
}

echo "\n=== COMPLETADO ===\n";
