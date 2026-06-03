<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";
require_once ABSPATH . "wp-admin/includes/media.php";
require_once ABSPATH . "wp-admin/includes/file.php";
require_once ABSPATH . "wp-admin/includes/image.php";

echo "=== COMPLETANDO RIVER PLATE INFO ===\n\n";

// ============================================================
// 1. CORREGIR JUGADORES EXISTENTES
// ============================================================
echo "--- 1. CORRIGIENDO JUGADORES ---\n";

$fix_players = [
    911 => ["sp_number" => 1,  "sp_position" => "Arquero",       "sp_nationality" => "Argentina"],
    914 => ["sp_number" => 6,  "sp_position" => "Defensor",       "sp_nationality" => "Chile"],
    917 => ["sp_number" => 3,  "sp_position" => "Defensor",       "sp_nationality" => "Argentina"],
    920 => ["sp_number" => 24, "sp_position" => "Mediocampista",  "sp_nationality" => "Argentina"],
    923 => ["sp_number" => 10, "sp_position" => "Mediocampista",  "sp_nationality" => "Argentina"],
    926 => ["sp_number" => 9,  "sp_position" => "Delantero",      "sp_nationality" => "Colombia"],
    929 => ["sp_number" => 11, "sp_position" => "Delantero",      "sp_nationality" => "Argentina"],
    932 => ["sp_number" => 29, "sp_position" => "Mediocampista",  "sp_nationality" => "Argentina"],
    935 => ["sp_number" => 14, "sp_position" => "Defensor",       "sp_nationality" => "Argentina"],
    938 => ["sp_number" => 18, "sp_position" => "Mediocampista",  "sp_nationality" => "Argentina"],
    941 => ["sp_number" => 36, "sp_position" => "Delantero",      "sp_nationality" => "Argentina"],
    1088 => ["sp_number" => 4,  "sp_position" => "Defensor",      "sp_nationality" => "Argentina", "post_title" => "Gonzalo Montiel"],
    1091 => ["sp_number" => 5,  "sp_position" => "Mediocampista", "sp_nationality" => "Argentina", "post_title" => "Fausto Vera"],
    1094 => ["sp_number" => 7,  "sp_position" => "Delantero",     "sp_nationality" => "Argentina", "post_title" => "Sebastián Driussi"],
];

foreach ($fix_players as $id => $data) {
    if (isset($data["post_title"])) {
        wp_update_post(["ID" => $id, "post_title" => $data["post_title"]]);
        $title = $data["post_title"];
        unset($data["post_title"]);
    } else {
        $p = get_post($id);
        $title = $p ? $p->post_title : "???";
    }
    foreach ($data as $key => $val) {
        update_post_meta($id, $key, $val);
    }
    $num = $data["sp_number"];
    $pos = $data["sp_position"];
    echo "  OK: #$num $title ($pos)\n";
}

// ============================================================
// 2. CREAR JUGADORES ADICIONALES
// ============================================================
echo "\n--- 2. CREANDO MAS JUGADORES ---\n";

$new_players = [
    ["title" => "Jeremías Ledesma",    "number" => 25, "position" => "Arquero",       "nationality" => "Argentina"],
    ["title" => "Marcos Acuña",        "number" => 21, "position" => "Defensor",      "nationality" => "Argentina"],
    ["title" => "Fabricio Bustos",     "number" => 16, "position" => "Defensor",      "nationality" => "Argentina"],
    ["title" => "Ramiro Funes Mori",   "number" => 2,  "position" => "Defensor",      "nationality" => "Argentina"],
    ["title" => "Milton Casco",        "number" => 20, "position" => "Defensor",      "nationality" => "Argentina"],
    ["title" => "Matías Kranevitter",  "number" => 8,  "position" => "Mediocampista", "nationality" => "Argentina"],
    ["title" => "Giuliano Galoppo",    "number" => 17, "position" => "Mediocampista", "nationality" => "Argentina"],
    ["title" => "Maximiliano Meza",    "number" => 22, "position" => "Mediocampista", "nationality" => "Argentina"],
    ["title" => "Facundo Buonanotte",  "number" => 30, "position" => "Mediocampista", "nationality" => "Argentina"],
    ["title" => "Agustín Ruberto",     "number" => 32, "position" => "Delantero",     "nationality" => "Argentina"],
    ["title" => "Ian Subiabre",        "number" => 19, "position" => "Delantero",     "nationality" => "Argentina"],
];

$all_player_ids = array_keys($fix_players); // IDs existentes

foreach ($new_players as $p) {
    $id = wp_insert_post([
        "post_title" => $p["title"],
        "post_type" => "sp_player",
        "post_status" => "publish",
    ]);
    if ($id && !is_wp_error($id)) {
        update_post_meta($id, "sp_number", $p["number"]);
        update_post_meta($id, "sp_position", $p["position"]);
        update_post_meta($id, "sp_nationality", $p["nationality"]);
        $all_player_ids[] = $id;
        echo "  OK: #{$p["number"]} {$p["title"]} ({$p["position"]}) ID=$id\n";
    }
}

// ============================================================
// 3. ASIGNAR JUGADORES A LA LISTA (ID=944)
// ============================================================
echo "\n--- 3. ASIGNANDO JUGADORES A LA LISTA ---\n";

// sp_list espera un array de IDs o string separado por comas
update_post_meta(944, "sp_list", $all_player_ids);
// Tambien actualizar sp_players (meta key alternativa)
update_post_meta(944, "sp_players", $all_player_ids);
echo "  " . count($all_player_ids) . " jugadores asignados a Plantilla (ID=944)\n";

// ============================================================
// 4. CREAR EVENTOS PASADOS CON RESULTADOS
// ============================================================

// Necesito crear equipos rivales primero para la tabla
echo "\n--- 4. CREANDO EQUIPOS RIVALES ---\n";

$rivales = [
    "Boca Juniors", "San Lorenzo", "Racing Club", "Independiente",
    "Talleres", "Vélez Sarsfield", "Estudiantes LP", "Huracán",
    "Godoy Cruz", "Rosario Central", "Lanús", "Belgrano",
    "Newell's Old Boys", "Banfield", "Defensa y Justicia", "Argentinos Juniors",
    "Platense", "Sarmiento", "Tigre", "Central Córdoba"
];

$river_team_id = null;
$rival_team_ids = [];

// Buscar el team de River (debe existir de antes)
$river_team = get_posts(["post_type"=>"sp_team","posts_per_page"=>1,"title"=>"River Plate"]);
if ($river_team) {
    $river_team_id = $river_team[0]->ID;
    echo "  River Plate team ID=$river_team_id\n";
} else {
    // Crear River team
    $river_team_id = wp_insert_post(["post_title"=>"River Plate","post_type"=>"sp_team","post_status"=>"publish"]);
    echo "  River Plate creado ID=$river_team_id\n";
}

foreach ($rivales as $nombre) {
    $existing = get_posts(["post_type"=>"sp_team","title"=>$nombre,"posts_per_page"=>1]);
    if ($existing) {
        $rival_team_ids[$nombre] = $existing[0]->ID;
    } else {
        $id = wp_insert_post(["post_title"=>$nombre,"post_type"=>"sp_team","post_status"=>"publish"]);
        if ($id && !is_wp_error($id)) {
            $rival_team_ids[$nombre] = $id;
        }
    }
}
echo "  " . count($rival_team_ids) . " equipos rivales listos\n";

// ============================================================
// 5. CREAR PARTIDOS PASADOS (con resultados)
// ============================================================
echo "\n--- 5. CREANDO FIXTURE COMPLETO ---\n";

// Simular temporada 2026: 19 fechas, mitad jugadas
$fixture = [
    // Fecha, Local, Visitante, Goles L, Goles V, Estado
    ["2026-02-02", "River Plate", "Belgrano",            3, 0, "publish"],
    ["2026-02-09", "Central Córdoba",  "River Plate",    1, 2, "publish"],
    ["2026-02-16", "River Plate", "Racing Club",         1, 1, "publish"],
    ["2026-02-23", "Banfield", "River Plate",            0, 3, "publish"],
    ["2026-03-02", "River Plate", "Estudiantes LP",      2, 1, "publish"],
    ["2026-03-09", "Huracán", "River Plate",             1, 1, "publish"],
    ["2026-03-16", "River Plate", "Talleres",             2, 0, "publish"],
    ["2026-03-30", "Newell's Old Boys", "River Plate",   0, 1, "publish"],
    ["2026-04-06", "River Plate", "Rosario Central",     3, 1, "publish"],
    ["2026-04-13", "Defensa y Justicia", "River Plate",  2, 4, "publish"],
    ["2026-04-20", "River Plate", "Argentinos Juniors",  1, 0, "publish"],
    ["2026-04-27", "Platense", "River Plate",            0, 0, "publish"],
    ["2026-05-04", "River Plate", "Vélez Sarsfield",     2, 1, "publish"],
    ["2026-05-11", "Sarmiento", "River Plate",           0, 3, "publish"],
    // Proximos partidos (future)
    ["2026-05-17", "River Plate", "San Lorenzo",          0, 0, "future"],
    ["2026-05-24", "River Plate", "Boca Juniors",         0, 0, "future"],
    ["2026-05-31", "Racing Club", "River Plate",          0, 0, "future"],
    ["2026-06-07", "River Plate", "Independiente",        0, 0, "future"],
    ["2026-06-14", "Godoy Cruz", "River Plate",           0, 0, "future"],
];

$event_ids = [];
foreach ($fixture as $f) {
    list($date, $local, $visita, $gl, $gv, $status) = $f;

    $title = "$local vs $visita";

    $event_id = wp_insert_post([
        "post_title" => $title,
        "post_type" => "sp_event",
        "post_status" => $status,
        "post_date" => "$date 18:00:00",
    ]);

    if ($event_id && !is_wp_error($event_id)) {
        update_post_meta($event_id, "sp_date", $date);
        update_post_meta($event_id, "sp_time", date("H:i", strtotime("21:00") - rand(0, 7200)));
        update_post_meta($event_id, "sp_venue", $local === "River Plate" ? "El Monumental" : "Visitante");

        // Asignar equipos
        $local_id = ($local === "River Plate") ? $river_team_id : ($rival_team_ids[$local] ?? 0);
        $visita_id = ($visita === "River Plate") ? $river_team_id : ($rival_team_ids[$visita] ?? 0);

        if ($local_id && $visita_id) {
            update_post_meta($event_id, "sp_team", [$local_id, $visita_id]);
        }

        // Resultados
        if ($status === "publish") {
            update_post_meta($event_id, "sp_results", [
                $local_id => ["goals" => $gl, "outcome" => ($gl > $gv ? "win" : ($gl < $gv ? "loss" : "draw"))],
                $visita_id => ["goals" => $gv, "outcome" => ($gv > $gl ? "win" : ($gv < $gl ? "loss" : "draw"))],
            ]);
        }

        $event_ids[] = $event_id;
        $icono = ($status === "future") ? "⏳" : "✅";
        $resultado = ($status === "publish") ? " ($gl-$gv)" : "";
        echo "  $icono $date: $title$resultado (ID=$event_id)\n";
    }
}

// Actualizar los eventos viejos que ya existian (968, 971, 974, 977) - cambiar status o eliminar
$old_events = [968, 971, 974, 977];
foreach ($old_events as $eid) {
    $ev = get_post($eid);
    if ($ev) {
        $title = $ev->post_title;
        // Ver si ya esta cubierto por el nuevo fixture
        $duplicate = false;
        foreach ($fixture as $f) {
            if (strpos($title, $f[1]) !== false && strpos($title, $f[2]) !== false) {
                $duplicate = true;
                break;
            }
        }
        if ($duplicate) {
            wp_delete_post($eid, true);
            echo "  Eliminado duplicado ID=$eid ($title)\n";
        }
    }
}

// ============================================================
// 6. CONFIGURAR TABLA DE POSICIONES (ID=947)
// ============================================================
echo "\n--- 6. CONFIGURANDO TABLA DE POSICIONES ---\n";

// Asignar TODOS los equipos a la tabla
$all_team_ids = array_merge([$river_team_id], array_values($rival_team_ids));
update_post_meta(947, "sp_teams", $all_team_ids);
update_post_meta(947, "sp_team", $river_team_id); // Equipo principal
echo "  " . count($all_team_ids) . " equipos asignados a la tabla (ID=947)\n";

// 7. ACTUALIZAR PAGINA TIENDA
echo "\n--- 7. ACTUALIZANDO TIENDA OFICIAL ---\n";

$tienda = get_page_by_path("tienda");
if ($tienda) {
    $tienda_content = '<!-- wp:heading {"className":"river-section-title"} --><h2>Tienda Oficial River Plate</h2><!-- /wp:heading -->

<!-- wp:paragraph --><p>Productos oficiales del Más Grande conseguidos a través de MercadoLibre. Todos los productos que ves acá son de afiliados.</p><!-- /wp:paragraph -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Camisetas</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[papafpro_produtos_categoria search="camiseta river plate" limit="6" columns="3"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Merchandising</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[papafpro_produtos_categoria search="river plate merchandising gorra bandera" limit="6" columns="3"]<!-- /wp:shortcode -->

<!-- wp:heading {"className":"river-section-title"} --><h2>Destacados</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[papafpro_produtos limit="9" columns="3"]<!-- /wp:shortcode -->
';

    wp_update_post(["ID" => $tienda->ID, "post_content" => $tienda_content]);
    echo "  Tienda (ID={$tienda->ID}) actualizada con productos PAF\n";
}

// 8. ACTUALIZAR PLANTILLA CON MAS INFO
echo "\n--- 8. ACTUALIZANDO PLANTILLA ---\n";
$plantilla = get_page_by_path("plantilla");
if ($plantilla) {
    $plant_content = '<!-- wp:heading {"className":"river-section-title"} --><h2>Plantilla Profesional 2026</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Conocé a los jugadores que defienden la banda roja esta temporada.</p><!-- /wp:paragraph -->
<!-- wp:shortcode -->[player_list id="944" columns="number,name,position,nationality"]<!-- /wp:shortcode -->
<!-- wp:heading {"className":"river-section-title"} --><h2>Cuerpo Técnico</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[staff_gallery id="945" columns="4"]<!-- /wp:shortcode -->
';
    wp_update_post(["ID" => $plantilla->ID, "post_content" => $plant_content]);
    echo "  Plantilla (ID={$plantilla->ID}) actualizada\n";
}

// 9. ACTUALIZAR INICIO CON MEJORES SHORTCODES
echo "\n--- 9. ACTUALIZANDO INICIO ---\n";
$inicio = get_page_by_path("inicio");
if ($inicio) {
    $inicio_content = '<!-- wp:cover {"dimRatio":50,"overlayColor":"black","minHeight":450,"align":"full","className":"river-hero"} -->
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
<!-- wp:shortcode -->[league_table id="947" number="10" columns="pos,team,w,d,l,pts"]<!-- /wp:shortcode -->
';
    wp_update_post(["ID" => $inicio->ID, "post_content" => $inicio_content]);
    echo "  Inicio (ID={$inicio->ID}) actualizada\n";
}

// 10. ACTUALIZAR CALENDARIO
echo "\n--- 10. ACTUALIZANDO CALENDARIO ---\n";
$calendario = get_page_by_path("calendario");
if ($calendario) {
    $cal_content = '<!-- wp:heading {"className":"river-section-title"} --><h2>Próximos Partidos</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_list status="future" number="20"]<!-- /wp:shortcode -->
<!-- wp:heading {"className":"river-section-title"} --><h2>Resultados</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_results number="20"]<!-- /wp:shortcode -->
<!-- wp:heading {"className":"river-section-title"} --><h2>Tabla de Posiciones</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[league_table id="947" columns="pos,team,w,d,l,gf,ga,gd,pts"]<!-- /wp:shortcode -->
';
    wp_update_post(["ID" => $calendario->ID, "post_content" => $cal_content]);
    echo "  Calendario (ID={$calendario->ID}) actualizada\n";
}

echo "\n=== COMPLETADO ===\n";
echo "Total jugadores: " . count($all_player_ids) . "\n";
echo "Total equipos: " . (1 + count($rival_team_ids)) . "\n";
echo "Total eventos: " . count($fixture) . "\n";
echo "Páginas actualizadas: Inicio, Plantilla, Calendario, Tienda\n";
