<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== MU-PLUGIN CHECK ===\n";
$mu_file = WP_CONTENT_DIR . "/mu-plugins/wa-river-club.php";
echo "File exists: " . (file_exists($mu_file) ? "SI" : "NO") . "\n";
echo "File size: " . filesize($mu_file) . "\n";

// Syntax check
$code = file_get_contents($mu_file);
echo "PHP syntax: ";
$tmp = tempnam(sys_get_temp_dir(), "phpcheck");
file_put_contents($tmp, $code);
exec("php -l " . escapeshellarg($tmp) . " 2>&1", $out, $rc);
echo ($rc === 0 ? "OK" : "ERROR: " . implode("\n", $out)) . "\n";
unlink($tmp);

echo "\n=== ENQUEUE TEST ===\n";
do_action("wp_enqueue_scripts");
global $wp_styles;
echo "Styles enqueued:\n";
foreach ($wp_styles->queue as $h) {
    $src = $wp_styles->registered[$h]->src ?? "???";
    echo "  $h -> $src\n";
}

echo "\n=== RUN HOOKS MANUALLY ===\n";
// Simular lo que haria wp_head
do_action("wp_enqueue_scripts");
$wp_styles->do_items();
echo "Done\n";
