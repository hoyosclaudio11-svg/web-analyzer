<?php
/**
 * Web Analyzer - Bridge para gestionar menus
 */
define('WP_USE_THEMES', false);
require_once __DIR__ . '/wp-load.php';

// Token via variable de entorno o constante de WordPress
$token = getenv('WA_BRIDGE_TOKEN') ?: (defined('WA_BRIDGE_TOKEN') ? WA_BRIDGE_TOKEN : null);
if (!$token || ($_POST['token'] ?? '') !== $token) {
    http_response_code(403);
    die('Acceso denegado');
}

$action = $_POST['action'] ?? '';

// =====================================================================
// LISTAR MENUS
// =====================================================================
if ($action === 'list_menus') {
    $menus = wp_get_nav_menus();
    $result = [];
    foreach ($menus as $menu) {
        $locations = get_nav_menu_locations();
        $assigned = [];
        foreach ($locations as $loc => $id) {
            if ($id == $menu->term_id) $assigned[] = $loc;
        }
        $result[] = [
            'id' => $menu->term_id,
            'name' => $menu->name,
            'slug' => $menu->slug,
            'locations' => $assigned,
        ];
    }
    header('Content-Type: application/json');
    echo json_encode($result, JSON_UNESCAPED_UNICODE);
    exit;
}

// =====================================================================
// LISTAR ITEMS DE UN MENU
// =====================================================================
if ($action === 'list_items') {
    $menu_id = intval($_POST['menu_id'] ?? 0);
    $items = wp_get_nav_menu_items($menu_id);
    $result = [];
    if ($items) {
        foreach ($items as $item) {
            $result[] = [
                'id' => $item->ID,
                'title' => $item->title,
                'url' => $item->url,
                'parent' => $item->menu_item_parent,
                'order' => $item->menu_order,
            ];
        }
    }
    header('Content-Type: application/json');
    echo json_encode($result, JSON_UNESCAPED_UNICODE);
    exit;
}

// =====================================================================
// LISTAR THEME LOCATIONS
// =====================================================================
if ($action === 'list_locations') {
    $locations = get_nav_menu_locations();
    $registered = get_registered_nav_menus();
    $result = ['assigned' => $locations, 'registered' => $registered];
    header('Content-Type: application/json');
    echo json_encode($result, JSON_UNESCAPED_UNICODE);
    exit;
}

// =====================================================================
// AGREGAR ITEM A MENU
// =====================================================================
if ($action === 'add_item') {
    $menu_id = intval($_POST['menu_id'] ?? 0);
    $title = $_POST['title'] ?? '';
    $url = $_POST['url'] ?? '';
    $position = intval($_POST['position'] ?? 0);

    $item_id = wp_update_nav_menu_item($menu_id, 0, [
        'menu-item-title' => $title,
        'menu-item-url' => $url,
        'menu-item-status' => 'publish',
        'menu-item-position' => $position,
    ]);

    if (is_wp_error($item_id)) {
        http_response_code(500);
        die('Error: ' . $item_id->get_error_message());
    }
    echo 'OK|item_id=' . $item_id;
    exit;
}

die('Accion no reconocida: ' . $action);
