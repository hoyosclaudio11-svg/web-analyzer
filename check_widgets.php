<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== WIDGETS ACTIVOS ===\n\n";
$sidebars = wp_get_sidebars_widgets();
foreach ($sidebars as $sidebar_id => $widgets) {
    if ($sidebar_id === "wp_inactive_widgets") continue;
    if (empty($widgets)) continue;
    echo "--- $sidebar_id ---\n";
    foreach ($widgets as $widget_id) {
        echo "  $widget_id\n";
        // Parse widget ID to get type and instance
        $parts = explode("-", $widget_id);
        $type = implode("-", array_slice($parts, 0, -1));
        $instance = end($parts);

        $widget_data = get_option("widget_" . $type);
        if ($widget_data && isset($widget_data[$instance])) {
            $data = $widget_data[$instance];
            if (isset($data["text"])) echo "    text: " . substr($data["text"], 0, 200) . "\n";
            if (isset($data["content"])) echo "    content: " . substr($data["content"], 0, 200) . "\n";
            if (isset($data["title"])) echo "    title: " . $data["title"] . "\n";
        }
    }
    echo "\n";
}

echo "=== FIN ===\n";
