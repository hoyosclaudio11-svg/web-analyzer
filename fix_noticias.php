<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== ARREGLANDO PAGINA NOTICIAS (ID=875) ===\n\n";

$noticias = get_page_by_path("noticias");
if (!$noticias) { echo "Pagina no encontrada\n"; exit; }

echo "Contenido antes:\n" . $noticias->post_content . "\n\n";

// Reemplazar el shortcode roto por el bloque nativo
$old = '<!-- wp:shortcode -->[latest_posts number="12" columns="2"]<!-- /wp:shortcode -->';
$new = '<!-- wp:latest-posts {"postsToShow":12,"displayPostContent":false,"displayPostDate":true,"displayFeaturedImage":true,"featuredImageAlign":"left","featuredImageSizeSlug":"medium","columns":2,"excerptLength":30} /-->';

$content = str_replace($old, $new, $noticias->post_content);

$result = wp_update_post(["ID" => $noticias->ID, "post_content" => $content]);
if ($result && !is_wp_error($result)) {
    echo "Pagina Noticias actualizada (ID=$result)\n";
} else {
    $err = is_wp_error($result) ? $result->get_error_message() : "retorno 0";
    echo "ERROR: $err\n";
}

echo "\nContenido despues:\n" . $content . "\n";
echo "\n=== COMPLETADO ===\n";
