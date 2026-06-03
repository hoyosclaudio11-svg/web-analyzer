<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== CSS CARGADO EN FRONT ===\n";
// Revisar que stylesheets estan registrados
global $wp_styles;
echo "Style handles en cola:\n";
foreach ($wp_styles->queue as $h) {
    $src = $wp_styles->registered[$h]->src ?? "???";
    echo "  $h -> $src\n";
}

echo "\n=== PAGE NOTICIAS RENDER ===\n";
$noticias = get_page_by_path("noticias");
if ($noticias) {
    $html = apply_filters("the_content", $noticias->post_content);
    // Buscar la estructura del bloque latest-posts
    if (strpos($html, "wp-block-latest-posts") !== false) {
        preg_match('/<ul class="[^"]*wp-block-latest-posts[^"]*"[^>]*>/', $html, $m);
        echo "UL tag: " . ($m[0] ?? "no encontrado") . "\n";
    }
    echo "HTML length: " . strlen($html) . "\n";
    echo substr($html, 0, 1500) . "\n";
}

echo "\n=== FIN ===\n";
