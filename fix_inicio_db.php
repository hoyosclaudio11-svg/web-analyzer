<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== ARREGLANDO INICIO (DIRECTO DB) ===\n\n";
global $wpdb;

$content = '<!-- wp:cover {"dimRatio":50,"overlayColor":"black","minHeight":450,"align":"full","className":"river-hero"} -->
<div class="wp-block-cover alignfull river-hero" style="min-height:450px"><div class="wp-block-cover__inner-container">
<h1 class="has-text-align-center has-white-color" style="font-size:48px;font-weight:900">Bienvenido al Club Atlético River Plate</h1>
<p class="has-text-align-center has-white-color" style="font-size:20px">El Más Grande, Lejos</p>
</div></div>
<!-- /wp:cover -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Últimas Noticias</h2><!-- /wp:heading -->
<!-- wp:latest-posts {"postsToShow":6,"displayPostDate":true,"displayFeaturedImage":true,"featuredImageSizeSlug":"medium","columns":3} /-->

<!-- wp:heading {"className":"river-section-title"} --><h2>Próximos Partidos</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_blocks status="future" number="3"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Últimos Resultados</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_blocks status="publish" number="3"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Tabla de Posiciones</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[league_table id="947"]<!-- /wp:shortcode -->
';

$result = $wpdb->update(
    $wpdb->posts,
    ["post_content" => $content],
    ["ID" => 866],
    ["%s"],
    ["%d"]
);

if ($result !== false) {
    echo "Inicio actualizada OK via DB\n";
    // Limpiar cache
    clean_post_cache(866);
} else {
    echo "DB ERROR: " . $wpdb->last_error . "\n";
}

echo "\nVerificacion: ";
$p = get_post(866);
echo "post_content length = " . strlen($p->post_content ?? "") . "\n";

echo "\n=== COMPLETADO ===\n";
