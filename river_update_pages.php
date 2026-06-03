<?php
/**
 * Actualizar paginas con IDs correctos de SportsPress
 */
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== ACTUALIZANDO SHORTCODES ===\n\n";

// Buscar IDs de SportsPress
$player_list = get_posts(["post_type" => "sp_list", "posts_per_page" => 1]);
$league_table = get_posts(["post_type" => "sp_table", "posts_per_page" => 1]);
$events = get_posts(["post_type" => "sp_event", "posts_per_page" => 5, "orderby" => "date", "order" => "DESC"]);
$teams = get_posts(["post_type" => "sp_team", "posts_per_page" => 1]);

$list_id = !empty($player_list) ? $player_list[0]->ID : 0;
$table_id = !empty($league_table) ? $league_table[0]->ID : 0;
$team_id = !empty($teams) ? $teams[0]->ID : 0;

echo "Player List ID: $list_id\n";
echo "League Table ID: $table_id\n";
echo "Team ID: $team_id\n";
echo "Events: " . count($events) . "\n";
foreach ($events as $e) {
    echo "  ID={$e->ID}: {$e->post_title}\n";
}

// Actualizar Inicio con IDs correctos
$inicio = get_page_by_path("inicio");
if ($inicio) {
    $content = '<!-- wp:cover {"dimRatio":50,"overlayColor":"black","minHeight":450,"align":"full","className":"river-hero"} -->
<div class="wp-block-cover alignfull river-hero" style="min-height:450px"><div class="wp-block-cover__inner-container">
<h1 class="has-text-align-center has-white-color" style="font-size:48px;font-weight:900">Bienvenido al Club Atlético River Plate</h1>
<p class="has-text-align-center has-white-color" style="font-size:20px">El Más Grande, Lejos</p>
</div></div>
<!-- /wp:cover -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Últimas Noticias</h2><!-- /wp:heading -->

<!-- wp:latest-posts {"postsToShow":6,"displayPostDate":true,"displayFeaturedImage":true,"featuredImageSizeSlug":"medium","columns":3} /-->

<!-- wp:heading {"className":"river-section-title"} --><h2>Próximo Partido</h2><!-- /wp:heading -->

<!-- wp:shortcode -->[event_blocks status="future" number="1"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Último Resultado</h2><!-- /wp:heading -->

<!-- wp:shortcode -->[event_blocks status="publish" number="1"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Tabla de Posiciones</h2><!-- /wp:heading -->

<!-- wp:shortcode -->[league_table id="' . $table_id . '"]<!-- /wp:shortcode -->';

    wp_update_post(["ID" => $inicio->ID, "post_content" => $content]);
    echo "\nInicio actualizada (IDs: table=$table_id)\n";
}

// Actualizar Plantilla
$plantilla = get_page_by_path("plantilla");
if ($plantilla) {
    $content = '<!-- wp:heading {"className":"river-section-title"} --><h2>Plantilla Profesional</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Conocé a los jugadores del Más Grande.</p><!-- /wp:paragraph -->
<!-- wp:shortcode -->[player_list id="' . $list_id . '" columns="number,name,position,nationality"]<!-- /wp:shortcode -->';
    wp_update_post(["ID" => $plantilla->ID, "post_content" => $content]);
    echo "Plantilla actualizada (list_id=$list_id)\n";
}

// Actualizar Calendario
$calendario = get_page_by_path("calendario");
if ($calendario) {
    $content = '<!-- wp:heading {"className":"river-section-title"} --><h2>Calendario de Partidos</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_list status="future" number="20"]<!-- /wp:shortcode -->
<!-- wp:heading {"className":"river-section-title"} --><h2>Resultados</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_results number="20"]<!-- /wp:shortcode -->';
    wp_update_post(["ID" => $calendario->ID, "post_content" => $content]);
    echo "Calendario actualizada\n";
}

echo "\n=== COMPLETADO ===\n";
