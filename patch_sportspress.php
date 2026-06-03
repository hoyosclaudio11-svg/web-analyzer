<?php
define("WP_USE_THEMES", false);
require_once __DIR__ . "/wp-load.php";

echo "=== PATCH SPORTSPRESS sp_array_value ===\n\n";

$file = WP_PLUGIN_DIR . "/sportspress/includes/sp-core-functions.php";
if (!file_exists($file)) {
    echo "ERROR: Archivo no encontrado\n";
    exit;
}

// Leer archivo
$content = file_get_contents($file);
$original = $content;

// Patch: hacer sp_array_value tolerante a non-array input (PHP 8.x fix)
$old_func = <<<'EOD'
if ( ! function_exists( 'sp_array_value' ) ) {
	function sp_array_value( $arr = array(), $key = 0, $default = null, $sanitize = false ) {
		$value = ( isset( $arr[ $key ] ) ? $arr[ $key ] : $default );
EOD;

$new_func = <<<'EOD'
if ( ! function_exists( 'sp_array_value' ) ) {
	function sp_array_value( $arr = array(), $key = 0, $default = null, $sanitize = false ) {
		// PHP 8.x fix: garantizar que $arr sea un array
		if ( ! is_array( $arr ) && ! is_object( $arr ) ) {
			return $default;
		}
		$value = ( isset( $arr[ $key ] ) ? $arr[ $key ] : $default );
EOD;

if (strpos($content, $old_func) !== false) {
    $content = str_replace($old_func, $new_func, $content);
    echo "Patch aplicado en sp_array_value\n";
} else {
    echo "NO se encontro la funcion sp_array_value con el formato esperado\n";
    echo "Buscando patron alternativo...\n";

    // Try to find it with different whitespace
    $pos = strpos($content, 'function sp_array_value');
    if ($pos !== false) {
        echo "Encontrada en posicion $pos\n";
        echo substr($content, $pos, 200) . "\n";
    }
}

// Segundo patch: también sp_array_between en la misma funcion
// La funcion main_results() llama a sp_array_value con datos que pueden ser string
// Verificamos si hay mas lugares problemáticos

if ($content !== $original) {
    // Hacer backup
    copy($file, $file . ".bak_20260515");
    echo "Backup creado: " . $file . ".bak_20260515\n";

    // Guardar
    file_put_contents($file, $content);
    echo "Archivo parcheado guardado\n";
} else {
    echo "No se hicieron cambios\n";
}

// Verificar
echo "\n--- Verificando [event_blocks status='publish' number='3'] ---\n";
$out = do_shortcode("[event_blocks status='publish' number='3']");
if (strpos($out, "Fatal error") !== false || strpos($out, "error crítico") !== false) {
    echo "SIGUE FALLANDO\n";
    // Revertir
    if ($content !== $original) {
        file_put_contents($file, $original);
        echo "REVERTIDO al original\n";
    }
} else {
    echo "FUNCIONA! Output: " . substr(strip_tags($out), 0, 400) . "\n";
}

echo "\n=== FIN ===\n";
