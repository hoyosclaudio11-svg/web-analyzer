<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== PAP AFILIADOS PRO CONFIG ===\n\n";

// Revisar opciones del plugin
$opts = get_option("papafpro_settings");
if ($opts) {
    echo "Settings: " . print_r($opts, true) . "\n";
}

// Revisar presets
$presets = get_option("papafpro_presets");
if ($presets) {
    echo "Presets: " . print_r($presets, true) . "\n";
}

// Buscar todas las opciones relacionadas con PAP
global $wpdb;
$pap_opts = $wpdb->get_results("SELECT option_name FROM {$wpdb->options} WHERE option_name LIKE '%papafpro%' OR option_name LIKE '%pap_afiliad%'");
echo "PAP Options:\n";
foreach ($pap_opts as $o) {
    $val = get_option($o->option_name);
    echo "  {$o->option_name}: ";
    if (is_array($val)) {
        echo print_r($val, true) . "\n";
    } else {
        echo (is_string($val) ? substr($val, 0, 500) : json_encode($val)) . "\n";
    }
}

echo "\n=== SHORTCODE HELP ===\n";
echo "papafpro_produtos: [papafpro_produtos]\n";
echo "papafpro_produtos_categoria: [papafpro_produtos_categoria]\n";
echo "papafpro_produtos_recentes: [papafpro_produtos_recentes]\n";
echo "papafpro_preset: [papafpro_preset]\n";
echo "papafpro_link: [papafpro_link]\n";

echo "\n=== FIN ===\n";
