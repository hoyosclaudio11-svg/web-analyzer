<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== ARREGLANDO COLUMNAS EN PAGINAS ===\n\n";

// Pagina Noticias (ID=875)
$noticias = get_page_by_path("noticias");
if ($noticias) {
    $old = '<!-- wp:latest-posts {"postsToShow":12,"displayPostContent":false,"displayPostDate":true,"displayFeaturedImage":true,"featuredImageAlign":"left","featuredImageSizeSlug":"medium","columns":2,"excerptLength":30} /-->';
    // Quitar featuredImageAlign para que el grid funcione
    $new = '<!-- wp:latest-posts {"postsToShow":12,"displayPostContent":false,"displayPostDate":true,"displayFeaturedImage":true,"featuredImageSizeSlug":"medium","columns":2,"excerptLength":30} /-->';

    $content = str_replace($old, $new, $noticias->post_content);
    wp_update_post(["ID" => $noticias->ID, "post_content" => $content]);
    echo "Noticias: OK\n";
}

// Pagina Inicio (ID=866) - Revisar si tiene featuredImageAlign:left
$inicio = get_page_by_path("inicio");
if ($inicio) {
    // Buscar el bloque latest-posts en Inicio
    $pattern = '/<!-- wp:latest-posts \{[^}]*"columns":(\d+)[^}]*\} \/-->/';
    if (preg_match($pattern, $inicio->post_content, $m)) {
        echo "Inicio bloque actual: {$m[0]}\n";
        // Reemplazar featuredImageAlign:left si existe
        $fixed = preg_replace('/"featuredImageAlign":"left",?/', '', $m[0]);
        $content = str_replace($m[0], $fixed, $inicio->post_content);
        wp_update_post(["ID" => $inicio->ID, "post_content" => $content]);
        echo "Inicio: OK ('featuredImageAlign:left' removido)\n";
    } else {
        echo "Inicio: bloque no encontrado con regex\n";
    }
}

echo "\n=== COMPLETADO ===\n";
