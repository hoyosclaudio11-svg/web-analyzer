<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== CONTENIDO DE PAGINAS ===\n\n";
foreach (["inicio","plantilla","calendario","noticias","tienda","contacto"] as $slug) {
    $p = get_page_by_path($slug);
    if ($p) {
        echo "--- /$slug (ID={$p->ID}) ---\n";
        echo $p->post_content . "\n\n";
    } else {
        echo "--- /$slug: NO EXISTE ---\n\n";
    }
}
