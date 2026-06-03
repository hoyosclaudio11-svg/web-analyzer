<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";
require_once ABSPATH . "wp-admin/includes/media.php";
require_once ABSPATH . "wp-admin/includes/file.php";
require_once ABSPATH . "wp-admin/includes/image.php";

echo "=== LOGO + CSS FIX ===\n\n";

// 1. Verificar y forzar el logo
echo "1. LOGO\n";
$logo_id = get_theme_mod("custom_logo");
echo "   custom_logo ID: $logo_id\n";

if ($logo_id) {
    $att = get_post($logo_id);
    echo "   Post type: " . ($att ? $att->post_type : "NO EXISTE") . "\n";
    $src = wp_get_attachment_url($logo_id);
    echo "   URL: $src\n";
    $file = get_attached_file($logo_id);
    echo "   File: $file\n";
    echo "   Existe: " . (file_exists($file) ? "SI" : "NO") . "\n";

    if (!file_exists($file)) {
        // Forzar la ruta correcta
        $correct_file = WP_CONTENT_DIR . "/uploads/logos/river-logo.png";
        if (file_exists($correct_file)) {
            update_post_meta($logo_id, "_wp_attached_file", "logos/river-logo.png");
            echo "   Ruta corregida a: logos/river-logo.png\n";

            // Regenerar metadata
            $meta = wp_generate_attachment_metadata($logo_id, $correct_file);
            wp_update_attachment_metadata($logo_id, $meta);
            echo "   Metadata regenerada\n";
        }
    }

    // Verificar thumbnail sizes
    $meta = wp_get_attachment_metadata($logo_id);
    echo "   Metadata: " . ($meta ? "SI (tiene " . count($meta) . " keys)" : "NO") . "\n";
}

// 2. Forzar el logo a aparecer con CSS como fallback
echo "\n2. Asegurando logo visible\n";
// El tema usa the_custom_logo() en header. Si no funciona, nuestro CSS
// puede inyectar el logo con ::before o similar.

echo "   Logo ID final: " . get_theme_mod("custom_logo") . "\n";
echo "   Logo URL: " . wp_get_attachment_url(get_theme_mod("custom_logo")) . "\n";

echo "\n=== COMPLETADO ===\n";
