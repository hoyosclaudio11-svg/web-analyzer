<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== TODOS LOS WIDGETS Y SU CONTENIDO ===\n\n";
$sidebars = wp_get_sidebars_widgets();
foreach ($sidebars as $sidebar_id => $widgets) {
    if ($sidebar_id === "wp_inactive_widgets") continue;
    if (empty($widgets)) continue;
    echo "=== $sidebar_id ===\n";
    foreach ($widgets as $widget_id) {
        $parts = explode("-", $widget_id);
        $type = implode("-", array_slice($parts, 0, -1));
        $instance = end($parts);

        $widget_data = get_option("widget_" . $type);
        echo "  [$widget_id] type=$type\n";
        if ($widget_data && isset($widget_data[$instance])) {
            foreach ($widget_data[$instance] as $k => $v) {
                if (is_string($v) && strlen($v) < 500) {
                    echo "    $k: $v\n";
                } elseif (is_string($v)) {
                    echo "    $k: " . substr($v, 0, 300) . "...\n";
                }
            }
        }
    }
}

echo "\n=== CUANTOS POSTS HAY? ===\n";
$counts = wp_count_posts("post");
echo "Posts: " . ($counts->publish ?? 0) . " publicados, " . ($counts->draft ?? 0) . " borrador\n";

echo "\n=== FRONT PAGE SETTINGS ===\n";
echo "show_on_front: " . get_option("show_on_front") . "\n";
echo "page_on_front: " . get_option("page_on_front") . "\n";
echo "page_for_posts: " . get_option("page_for_posts") . "\n";

echo "\n=== FIN ===\n";
