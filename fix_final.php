<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== FIX FINAL ===\n\n";

// ============================================================
// 1. ARREGLAR PLAYER LIST - Equipo correcto
// ============================================================
echo "--- 1. PLAYER LIST ---\n";
$river = get_posts(["post_type"=>"sp_team","title"=>"River Plate","posts_per_page"=>1]);
$team_id = $river[0]->ID;
echo "River Team ID: $team_id\n";

// Asignar el equipo correcto al player list
update_post_meta(944, "sp_team", $team_id);
echo "Player List sp_team actualizado a $team_id\n";

// Verificar shortcode
echo "Shortcode test: " . substr(do_shortcode('[player_list id="944"]'), 0, 300) . "\n";

// ============================================================
// 2. ACTUALIZAR PAGINAS - Dejar claro que NO es oficial
// ============================================================
echo "\n--- 2. ACTUALIZANDO TEXTOS ---\n";
global $wpdb;

// Inicio - Hero mas claro
$inicio_content = '<!-- wp:cover {"dimRatio":60,"overlayColor":"black","minHeight":400,"align":"full","className":"river-hero"} -->
<div class="wp-block-cover alignfull river-hero" style="min-height:400px"><div class="wp-block-cover__inner-container">
<h1 class="has-text-align-center has-white-color" style="font-size:44px;font-weight:900">River Plate Info</h1>
<p class="has-text-align-center has-white-color" style="font-size:18px">Sitio de informacion y noticias sobre el Club Atlético River Plate</p>
<p class="has-text-align-center" style="font-size:12px;color:#aaa;margin-top:12px">Sitio no oficial · Creado por hinchas · No afiliado al club</p>
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

$wpdb->update($wpdb->posts, ["post_content"=>$inicio_content], ["ID"=>866], ["%s"], ["%d"]);
clean_post_cache(866);
echo "Inicio actualizada (disclaimer agregado)\n";

// Tienda - Cambiar nombre, quitar "Oficial"
$tienda_content = '<!-- wp:heading {"className":"river-section-title"} --><h2>Productos de River Plate en MercadoLibre</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Productos relacionados con River Plate a traves del programa de afiliados de MercadoLibre. Este sitio no es la tienda oficial del club.</p><!-- /wp:paragraph -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Camisetas</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[papafpro_produtos_categoria search="camiseta river plate" limit="6" columns="3"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Merchandising</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[papafpro_produtos_categoria search="river plate merchandising gorra bandera" limit="6" columns="3"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Mas Productos</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[papafpro_produtos limit="9" columns="3"]<!-- /wp:shortcode -->
';

$wpdb->update($wpdb->posts, ["post_content"=>$tienda_content, "post_title"=>"Tienda"], ["ID"=>878], ["%s","%s"], ["%d"]);
clean_post_cache(878);
echo "Tienda actualizada (sin 'Oficial')\n";

// Tambien actualizar el titulo del menu para Tienda
$menu_items = wp_get_nav_menu_items("Menu Principal");
if ($menu_items) {
    foreach ($menu_items as $item) {
        if ($item->title === "Tienda Oficial" && $item->object_id == 878) {
            wp_update_nav_menu_item($item->menu_order, $item->ID, [
                "menu-item-title" => "Tienda",
                "menu-item-url" => $item->url,
                "menu-item-status" => "publish",
            ]);
            echo "Menu 'Tienda Oficial' -> 'Tienda' actualizado\n";
            break;
        }
    }
}

// ============================================================
// 3. VERIFICACION FINAL
// ============================================================
echo "\n--- 3. VERIFICACION ---\n";
echo "Pagina Inicio content length: " . strlen(get_post(866)->post_content) . "\n";
echo "Pagina Tienda title: " . get_post(878)->post_title . "\n";
echo "Player List sp_team: " . get_post_meta(944, "sp_team", true) . "\n";

echo "\n=== COMPLETADO ===\n";
