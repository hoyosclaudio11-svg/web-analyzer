<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== REVISANDO PAGINA INICIO ===\n\n";

$inicio = get_page_by_path("inicio");
if ($inicio) {
    echo "Inicio ID={$inicio->ID}\n";
    echo "Contenido actual:\n";
    echo $inicio->post_content . "\n\n";
} else {
    echo "Pagina Inicio no encontrada.\n";
}

echo "=== CORRIGIENDO ===\n";

// Solo reemplazar el shortcode roto, preservar el resto del contenido
$new_block = '<!-- wp:latest-posts {"postsToShow":12,"displayPostContent":false,"displayPostDate":true,"displayFeaturedImage":true,"featuredImageAlign":"left","featuredImageSizeSlug":"medium","columns":2,"excerptLength":30} /-->';

if ($inicio) {
    $content = $inicio->post_content;
    echo "Contenido TIENE shortcode roto: " . (strpos($content, '[latest_posts') !== false ? "SI" : "NO") . "\n";
    // Reemplazar cualquier variante de [latest_posts ...]
    $content = preg_replace('/\[latest_posts[^\]]*\]/', $new_block, $content);

    $result = wp_update_post([
        "ID" => $inicio->ID,
        "post_content" => $content
    ]);
    if ($result && !is_wp_error($result)) {
        echo "Pagina Inicio actualizada (ID=$result)\n";
    } else {
        $err = is_wp_error($result) ? $result->get_error_message() : "retorno 0";
        echo "ERROR: $err\n";
    }
}

echo "\n=== VERIFICANDO ===\n";
$inicio2 = get_page_by_path("inicio");
echo "Nuevo contenido:\n" . $inicio2->post_content . "\n";
echo "\n=== COMPLETADO ===\n";
