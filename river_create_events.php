<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== CREANDO EVENTOS SPORTSPRESS ===\n\n";

// Forzar init para registrar CPTs
do_action("init");

echo "sp_event registrado: " . (post_type_exists("sp_event") ? "SI" : "NO") . "\n";
echo "sp_team registrado: " . (post_type_exists("sp_team") ? "SI" : "NO") . "\n";

if (post_type_exists("sp_event")) {
    $partidos = [
        ["title" => "River Plate vs San Lorenzo", "date" => "2026-05-17", "time" => "19:30", "venue" => "El Monumental"],
        ["title" => "River Plate vs Boca Juniors", "date" => "2026-05-24", "time" => "17:00", "venue" => "El Monumental"],
        ["title" => "Racing vs River Plate", "date" => "2026-05-31", "time" => "21:00", "venue" => "El Cilindro"],
        ["title" => "River Plate vs Independiente", "date" => "2026-06-07", "time" => "20:00", "venue" => "El Monumental"],
    ];

    foreach ($partidos as $p) {
        $id = wp_insert_post([
            "post_title" => $p["title"],
            "post_type" => "sp_event",
            "post_status" => "publish",
            "post_date" => "2026-05-14 12:00:00"
        ]);

        if ($id && !is_wp_error($id)) {
            update_post_meta($id, "sp_date", $p["date"]);
            update_post_meta($id, "sp_time", $p["time"]);
            update_post_meta($id, "sp_venue", $p["venue"]);
            echo "  {$p["title"]}: CREADO (ID=$id)\n";
        } else {
            $err = is_wp_error($id) ? $id->get_error_message() : "retorno 0";
            echo "  {$p["title"]}: ERROR - $err\n";
        }
    }

    // Verificar
    $count = wp_count_posts("sp_event")->publish ?? 0;
    echo "\nTotal eventos: $count\n";

    $all = get_posts(["post_type" => "sp_event", "posts_per_page" => -1]);
    echo "get_posts: " . count($all) . "\n";
    foreach ($all as $e) {
        echo "  ID={$e->ID}: {$e->post_title} (status={$e->post_status})\n";
    }
} else {
    echo "No se pueden crear eventos sin el CPT registrado.\n";
}

echo "\n=== COMPLETADO ===\n";
