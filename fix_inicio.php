<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== ARREGLANDO INICIO ===\n\n";

$inicio = get_page_by_path("inicio");
if (!$inicio) { echo "No encontrada\n"; exit; }

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

$result = wp_update_post(["ID" => $inicio->ID, "post_content" => $content]);
if ($result && !is_wp_error($result)) {
    echo "Inicio actualizada OK (ID=$result)\n";
} else {
    $err = is_wp_error($result) ? $result->get_error_message() : "retorno 0";
    echo "ERROR: $err\n";
}

echo "\n=== COMPLETADO ===\n";
