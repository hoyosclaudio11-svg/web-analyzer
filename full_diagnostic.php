<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== 1. PLUGINS ===\n";
echo "SportsPress: " . (is_plugin_active("sportspress/sportspress.php") ? "SI" : "NO") . "\n";
// Buscar plugin de afiliados ML
$all_plugins = get_plugins();
foreach ($all_plugins as $path => $data) {
    if (stripos($data["Name"], "afiliad") !== false || stripos($data["Name"], "mercadolibre") !== false || stripos($data["Name"], "paf") !== false || stripos($data["Name"], "ML") !== false) {
        echo "Plugin: {$data["Name"]} (activo: " . (is_plugin_active($path) ? "SI" : "NO") . ")\n";
        echo "  Path: $path\n";
    }
}

echo "\n=== 2. SPORTSPRESS DATA ===\n";
foreach (["sp_team","sp_player","sp_event","sp_list","sp_table","sp_staff"] as $pt) {
    $count = wp_count_posts($pt)->publish ?? 0;
    echo "  $pt: $count\n";
}

echo "\n=== 3. PLAYERS ===\n";
$players = get_posts(["post_type"=>"sp_player","posts_per_page"=>-1,"orderby"=>"title","order"=>"ASC"]);
foreach ($players as $p) {
    $number = get_post_meta($p->ID, "sp_number", true);
    $pos = get_post_meta($p->ID, "sp_position", true);
    echo "  ID={$p->ID}: #$number {$p->post_title} ($pos)\n";
}

echo "\n=== 4. EVENTS ===\n";
$events = get_posts(["post_type"=>"sp_event","posts_per_page"=>-1,"orderby"=>"date","order"=>"ASC"]);
foreach ($events as $e) {
    $date = get_post_meta($e->ID, "sp_date", true);
    $time = get_post_meta($e->ID, "sp_time", true);
    $venue = get_post_meta($e->ID, "sp_venue", true);
    echo "  ID={$e->ID}: {$e->post_title} | $date $time | $venue\n";
}

echo "\n=== 5. PLAYER LIST (ID=944) ===\n";
$list = get_post(944);
if ($list) {
    echo "  Title: {$list->post_title}\n";
    $ids = get_post_meta(944, "sp_list", true);
    echo "  Players: " . (is_array($ids) ? implode(", ", $ids) : $ids) . "\n";
}

echo "\n=== 6. LEAGUE TABLE (ID=947) ===\n";
$table = get_post(947);
if ($table) {
    echo "  Title: {$table->post_title}\n";
    $teams = get_post_meta(947, "sp_teams", true);
    echo "  Teams: " . (is_array($teams) ? implode(", ", $teams) : $teams) . "\n";
}

echo "\n=== 7. PAGES CONTENT ===\n";
foreach (["inicio","plantilla","calendario","noticias","tienda","contacto"] as $s) {
    $p = get_page_by_path($s);
    if ($p) {
        echo "--- /$s (ID={$p->ID}) ---\n";
        echo $p->post_content . "\n\n";
    }
}

echo "\n=== 8. SHORTCODES DISPONIBLES ===\n";
global $shortcode_tags;
$relevant = [];
foreach ($shortcode_tags as $tag => $fn) {
    if (stripos($tag, "sp_") !== false || stripos($tag, "event") !== false || stripos($tag, "player") !== false || stripos($tag, "league") !== false || stripos($tag, "team") !== false || stripos($tag, "product") !== false || stripos($tag, "afiliad") !== false || stripos($tag, "paf") !== false || stripos($tag, "ml") !== false) {
        $relevant[] = $tag;
    }
}
echo implode(", ", $relevant) . "\n";
echo "Total shortcodes: " . count($shortcode_tags) . "\n";

echo "\n=== FIN ===\n";
