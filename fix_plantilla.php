<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== DIAGNOSTICO PLANTILLA ===\n\n";

// Check player list meta
$list_id = 944;
echo "Player List ID=$list_id\n";
echo "sp_list: "; var_dump(get_post_meta($list_id, "sp_list", true));
echo "sp_players: "; var_dump(get_post_meta($list_id, "sp_players", true));

// Check all meta for this post
echo "\nAll meta:\n";
$all_meta = get_post_meta($list_id);
foreach ($all_meta as $k => $v) {
    if ($k[0] !== "_") {
        echo "  $k: " . (is_array($v) ? implode(", ", $v) : $v) . "\n";
    }
}

// Check a player to verify the relationship works both ways
echo "\nPlayer ID=911 (Armani):\n";
$teams = get_post_meta(911, "sp_team", true);
echo "  sp_team: " . (is_array($teams) ? implode(", ", $teams) : $teams) . "\n";
$lists = get_post_meta(911, "sp_list", true);
echo "  sp_list: " . (is_array($lists) ? implode(", ", $lists) : $lists) . "\n";

// Check how many players are queryable
echo "\n=== PLAYERS IN DB ===\n";
$players = get_posts(["post_type"=>"sp_player","posts_per_page"=>-1,"orderby"=>"title","order"=>"ASC"]);
echo "Total: " . count($players) . "\n";
foreach ($players as $p) {
    $num = get_post_meta($p->ID, "sp_number", true);
    $pos = get_post_meta($p->ID, "sp_position", true);
    $nat = get_post_meta($p->ID, "sp_nationality", true);
    echo "  ID={$p->ID}: #$num {$p->post_title} ($pos / $nat)\n";
}

// Verify player list shortcode output
echo "\n=== SHORTCODE OUTPUT ===\n";
echo do_shortcode('[player_list id="944"]');

echo "\n=== FIN ===\n";
