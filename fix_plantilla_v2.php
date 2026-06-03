<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== ASIGNANDO JUGADORES AL EQUIPO ===\n\n";

// Buscar el equipo de River
$river = get_posts(["post_type"=>"sp_team","title"=>"River Plate","posts_per_page"=>1]);
$team_id = $river ? $river[0]->ID : 0;
echo "River Team ID: $team_id\n";

if (!$team_id) { echo "ERROR: No se encuentra el equipo de River\n"; exit; }

// Todos los jugadores
$players = get_posts(["post_type"=>"sp_player","posts_per_page"=>-1]);
echo "Total jugadores: " . count($players) . "\n";

$fixed = 0;
foreach ($players as $player) {
    // Asignar equipo actual
    update_post_meta($player->ID, "sp_team", $team_id);
    update_post_meta($player->ID, "sp_current_team", $team_id);
    $fixed++;
}

echo "Jugadores con equipo asignado: $fixed\n";

// Verificar
$armani = get_post(911);
echo "\nVerificacion Armani (ID=911):\n";
echo "  sp_team: " . get_post_meta(911, "sp_team", true) . "\n";
echo "  sp_current_team: " . get_post_meta(911, "sp_current_team", true) . "\n";

// Probar shortcode
echo "\n=== SHORTCODE OUTPUT ===\n";
echo do_shortcode('[player_list id="944"]');

echo "\n=== FIN ===\n";
