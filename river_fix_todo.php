<?php
/**
 * River Plate Info — Fix Integral
 * 1. Logo correcto
 * 2. SportsPress demo data
 * 3. Limpiar cache
 */
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";
require_once ABSPATH . "wp-admin/includes/plugin.php";
require_once ABSPATH . "wp-admin/includes/media.php";
require_once ABSPATH . "wp-admin/includes/file.php";
require_once ABSPATH . "wp-admin/includes/image.php";

echo "=== FIX INTEGRAL RIVER PLATE ===\n\n";

// ================================================================
// 1. LOGO — Cambiar a river-logo.png
// ================================================================
echo "1. LOGO\n";
$current_logo_id = get_theme_mod("custom_logo"); // ID=26, imagen vieja
$our_logo_path = WP_CONTENT_DIR . "/uploads/logos/river-logo.png";

if (file_exists($our_logo_path)) {
    // Ver si ya existe un attachment para nuestro logo
    $existing = get_posts([
        "post_type" => "attachment",
        "meta_key" => "_wp_attached_file",
        "meta_value" => "logos/river-logo.png",
        "posts_per_page" => 1
    ]);

    $logo_id = null;
    if (!empty($existing)) {
        $logo_id = $existing[0]->ID;
        echo "   Attachment ya existe (ID=$logo_id)\n";
    } else {
        // Crear nuevo attachment
        $upload_dir = wp_upload_dir();
        $filename = "river-logo.png";
        $file_path = $our_logo_path;

        $attach_id = wp_insert_attachment([
            "guid"           => $upload_dir["url"] . "/logos/$filename",
            "post_mime_type" => "image/png",
            "post_title"     => "River Plate Logo",
            "post_status"    => "inherit",
            "post_date"      => "2026-05-14 00:00:00"
        ], $file_path);

        if (!is_wp_error($attach_id)) {
            $meta = wp_generate_attachment_metadata($attach_id, $file_path);
            wp_update_attachment_metadata($attach_id, $meta);

            // Actualizar el _wp_attached_file para que apunte a logos/river-logo.png
            update_post_meta($attach_id, "_wp_attached_file", "logos/river-logo.png");

            $logo_id = $attach_id;
            echo "   Attachment creado (ID=$attach_id)\n";
        } else {
            echo "   ERROR: " . $attach_id->get_error_message() . "\n";
        }
    }

    if ($logo_id) {
        set_theme_mod("custom_logo", $logo_id);
        echo "   custom_logo actualizado a ID=$logo_id\n";
        $url = wp_get_attachment_url($logo_id);
        echo "   URL del logo: $url\n";
    }
} else {
    echo "   ERROR: river-logo.png no encontrado\n";
}

// ================================================================
// 2. SPORTSPRESS — Crear datos demo
// ================================================================
echo "\n2. SPORTSPRESS DEMO DATA\n";

if (!is_plugin_active("sportspress/sportspress.php")) {
    echo "   SportsPress no activo. Abortando demo data.\n";
} else {
    // Crear equipo River Plate
    $team_id = null;
    $existing_teams = get_posts(["post_type" => "sp_team", "posts_per_page" => 1]);
    if (!empty($existing_teams)) {
        $team_id = $existing_teams[0]->ID;
        echo "   Equipo ya existe: {$existing_teams[0]->post_title} (ID=$team_id)\n";
    } else {
        $team_id = wp_insert_post([
            "post_title" => "River Plate",
            "post_type" => "sp_team",
            "post_status" => "publish"
        ]);
        echo "   Equipo River Plate creado (ID=$team_id)\n";
    }

    // Crear jugadores
    $jugadores = [
        ["name" => "Franco Armani", "number" => "1", "position" => "Arquero", "nationality" => "Argentina"],
        ["name" => "Paulo Díaz", "number" => "6", "position" => "Defensor", "nationality" => "Chile"],
        ["name" => "Germán Pezzella", "number" => "3", "position" => "Defensor", "nationality" => "Argentina"],
        ["name" => "Enzo Pérez", "number" => "24", "position" => "Mediocampista", "nationality" => "Argentina"],
        ["name" => "Ignacio Fernández", "number" => "10", "position" => "Mediocampista", "nationality" => "Argentina"],
        ["name" => "Miguel Borja", "number" => "9", "position" => "Delantero", "nationality" => "Colombia"],
        ["name" => "Facundo Colidio", "number" => "11", "position" => "Delantero", "nationality" => "Argentina"],
        ["name" => "Rodrigo Aliendro", "number" => "29", "position" => "Mediocampista", "nationality" => "Argentina"],
        ["name" => "Leandro González Pirez", "number" => "14", "position" => "Defensor", "nationality" => "Argentina"],
        ["name" => "Gonzalo Martínez", "number" => "18", "position" => "Mediocampista", "nationality" => "Argentina"],
        ["name" => "Pablo Solari", "number" => "36", "position" => "Delantero", "nationality" => "Argentina"],
    ];

    $player_ids = [];
    echo "\n   Jugadores:\n";
    foreach ($jugadores as $j) {
        $existing = get_posts([
            "post_type" => "sp_player",
            "title" => $j["name"],
            "posts_per_page" => 1
        ]);
        if (!empty($existing)) {
            $player_ids[] = $existing[0]->ID;
            echo "     {$j["name"]}: YA EXISTE (ID={$existing[0]->ID})\n";
        } else {
            $pid = wp_insert_post([
                "post_title" => $j["name"],
                "post_type" => "sp_player",
                "post_status" => "publish"
            ]);
            if ($pid) {
                // Meta del jugador
                update_post_meta($pid, "sp_number", $j["number"]);
                update_post_meta($pid, "sp_position", $j["position"]);
                update_post_meta($pid, "sp_nationality", $j["nationality"]);
                update_post_meta($pid, "sp_current_team", $team_id);
                $player_ids[] = $pid;
                echo "     {$j["name"]}: CREADO (#{$j["number"]}, {$j["position"]})\n";
            }
        }
    }

    // Crear lista de jugadores (player_list)
    $list_id = null;
    $existing_lists = get_posts(["post_type" => "sp_list", "posts_per_page" => 1]);
    if (!empty($existing_lists)) {
        $list_id = $existing_lists[0]->ID;
        echo "\n   Player List ya existe (ID=$list_id)\n";
    } else {
        $list_id = wp_insert_post([
            "post_title" => "Plantilla River Plate",
            "post_type" => "sp_list",
            "post_status" => "publish"
        ]);
        echo "\n   Player List creada (ID=$list_id)\n";
    }
    // Asignar jugadores a la lista
    update_post_meta($list_id, "sp_players", $player_ids);
    update_post_meta($list_id, "sp_team", $team_id);
    echo "   " . count($player_ids) . " jugadores asignados a lista\n";

    // Crear tabla de posiciones
    $table_id = null;
    $existing_tables = get_posts(["post_type" => "sp_table", "posts_per_page" => 1]);
    if (!empty($existing_tables)) {
        $table_id = $existing_tables[0]->ID;
        echo "\n   Tabla ya existe (ID=$table_id)\n";
    } else {
        $table_id = wp_insert_post([
            "post_title" => "Liga Profesional 2026",
            "post_type" => "sp_table",
            "post_status" => "publish"
        ]);
        echo "\n   Tabla de posiciones creada (ID=$table_id)\n";
    }
    update_post_meta($table_id, "sp_team", $team_id);

    // Crear algunos partidos (events)
    $partidos = [
        ["title" => "River Plate vs Boca Juniors", "date" => "2026-05-24", "time" => "17:00", "venue" => "El Monumental"],
        ["title" => "Racing vs River Plate", "date" => "2026-05-31", "time" => "21:00", "venue" => "El Cilindro"],
        ["title" => "River Plate vs San Lorenzo", "date" => "2026-05-17", "time" => "19:30", "venue" => "El Monumental"],
    ];

    echo "\n   Partidos:\n";
    foreach ($partidos as $p) {
        $existing = get_posts([
            "post_type" => "sp_event",
            "title" => $p["title"],
            "posts_per_page" => 1
        ]);
        if (!empty($existing)) {
            echo "     {$p["title"]}: YA EXISTE\n";
        } else {
            $eid = wp_insert_post([
                "post_title" => $p["title"],
                "post_type" => "sp_event",
                "post_status" => "publish",
                "post_date" => $p["date"] . " " . $p["time"]
            ]);
            if ($eid) {
                update_post_meta($eid, "sp_date", $p["date"]);
                update_post_meta($eid, "sp_time", $p["time"]);
                update_post_meta($eid, "sp_venue", $p["venue"]);
                update_post_meta($eid, "sp_team", [$team_id]);
                echo "     {$p["title"]}: CREADO ({$p["date"]} {$p["time"]})\n";
            }
        }
    }
}

// ================================================================
// 3. Limpiar caches
// ================================================================
echo "\n3. LIMPIANDO CACHES\n";
if (function_exists("wp_cache_flush")) {
    wp_cache_flush();
    echo "   Object cache limpiada\n";
}
global $wpdb;
$wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '%_transient_%'");
echo "   Transients limpiados\n";

echo "\n=== FIX COMPLETADO ===\n";
echo "Visita el sitio para ver los cambios.\n";
