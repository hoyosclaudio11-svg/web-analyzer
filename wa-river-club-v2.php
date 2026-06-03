<?php
/**
 * River Plate Info — Club de Futbol Profesional
 * Version 2 — CSS + Setup en admin-only
 */
if (!defined("ABSPATH")) exit;

/* ================================================================
   DEPURAR CSS DEL TEMA QUE INTERFIERE
   ================================================================ */
add_action("wp_enqueue_scripts", "river_nuke_css", 9999);
function river_nuke_css() {
    global $wp_styles;
    foreach ($wp_styles->queue as $h) {
        if (strpos($h,"newsup")!==false || strpos($h,"newstack")!==false ||
            strpos($h,"bootstrap")!==false || strpos($h,"font-awesome")!==false ||
            strpos($h,"owl")!==false || strpos($h,"animate")!==false ||
            strpos($h,"marquee")!==false || strpos($h,"smartmenus")!==false) {
            wp_dequeue_style($h); wp_deregister_style($h);
        }
    }
}

/* ================================================================
   SETUP INICIAL — Solo en admin, una vez
   ================================================================ */
add_action("admin_init", "wa_river_club_setup");
function wa_river_club_setup() {
    if (get_option("wa_river_club_setup_done")) return;

    require_once ABSPATH . "wp-admin/includes/plugin.php";
    require_once ABSPATH . "wp-admin/includes/media.php";
    require_once ABSPATH . "wp-admin/includes/file.php";
    require_once ABSPATH . "wp-admin/includes/image.php";

    // Activar SportsPress
    $sp = "sportspress/sportspress.php";
    if (file_exists(WP_PLUGIN_DIR . "/" . $sp) && !is_plugin_active($sp)) {
        activate_plugin($sp);
    }

    // Crear paginas
    $pages = [
        "inicio" => ["title" => "Inicio", "content" => '<!-- wp:cover {"dimRatio":50,"overlayColor":"black","minHeight":450,"align":"full","className":"river-hero"} -->
<div class="wp-block-cover alignfull river-hero" style="min-height:450px"><div class="wp-block-cover__inner-container">
<h1 class="has-text-align-center has-white-color" style="font-size:48px;font-weight:900">Bienvenido al Club Atletico River Plate</h1>
<p class="has-text-align-center has-white-color" style="font-size:20px">El Mas Grande, Lejos</p>
</div></div>
<!-- /wp:cover -->
<!-- wp:heading {"className":"river-section-title"} --><h2>Ultimas Noticias</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[latest_posts number="6" columns="3"]<!-- /wp:shortcode -->
<!-- wp:heading {"className":"river-section-title"} --><h2>Proximo Partido</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_list status="future" number="1"]<!-- /wp:shortcode -->
<!-- wp:heading {"className":"river-section-title"} --><h2>Ultimo Resultado</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_results number="1"]<!-- /wp:shortcode -->
<!-- wp:heading {"className":"river-section-title"} --><h2>Tabla de Posiciones</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[league_table number="1"]<!-- /wp:shortcode -->'],
        "plantilla" => ["title" => "Plantilla", "content" => '<!-- wp:heading {"className":"river-section-title"} --><h2>Plantilla Profesional</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Conoce a los jugadores del Mas Grande.</p><!-- /wp:paragraph -->
<!-- wp:shortcode -->[player_list number="50" columns="number,name,position,nationality"]<!-- /wp:shortcode -->'],
        "calendario" => ["title" => "Calendario", "content" => '<!-- wp:heading {"className":"river-section-title"} --><h2>Calendario de Partidos</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_list status="future" number="20"]<!-- /wp:shortcode -->
<!-- wp:heading {"className":"river-section-title"} --><h2>Resultados</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[event_results number="20"]<!-- /wp:shortcode -->'],
        "noticias" => ["title" => "Noticias", "content" => '<!-- wp:heading {"className":"river-section-title"} --><h2>Noticias de River Plate</h2><!-- /wp:heading -->
<!-- wp:shortcode -->[latest_posts number="12" columns="2"]<!-- /wp:shortcode -->'],
        "tienda" => ["title" => "Tienda Oficial", "content" => '<!-- wp:heading {"className":"river-section-title"} --><h2>Tienda Oficial</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Proximamente: camisetas oficiales, merchandising y mas productos del Mas Grande.</p><!-- /wp:paragraph -->'],
        "contacto" => ["title" => "Contacto", "content" => '<!-- wp:heading {"className":"river-section-title"} --><h2>Contacto</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Queres anunciar en River Plate Info? Tenes una primicia? Escribinos.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>Email: info@riverplate-info.com.ar</p><!-- /wp:paragraph -->']
    ];

    $page_ids = [];
    foreach ($pages as $slug => $data) {
        $existing = get_page_by_path($slug);
        if (!$existing) {
            $page_ids[$slug] = wp_insert_post([
                "post_title"   => $data["title"],
                "post_name"    => $slug,
                "post_content" => $data["content"],
                "post_status"  => "publish",
                "post_type"    => "page"
            ]);
        } else {
            $page_ids[$slug] = $existing->ID;
        }
    }

    // Menu
    $menu_name = "Menu Principal";
    $menu_exists = wp_get_nav_menu_object($menu_name);
    $menu_id = $menu_exists ? $menu_exists->term_id : wp_create_nav_menu($menu_name);

    $menu_items_order = ["inicio", "plantilla", "calendario", "noticias", "tienda", "contacto"];
    foreach ($menu_items_order as $i => $slug) {
        if (!isset($page_ids[$slug]) || !isset($pages[$slug])) continue;
        $existing_items = wp_get_nav_menu_items($menu_id);
        $found = false;
        foreach ($existing_items as $item) {
            if ($item->object_id == $page_ids[$slug]) { $found = true; break; }
        }
        if (!$found) {
            wp_update_nav_menu_item($menu_id, 0, [
                "menu-item-title"  => $pages[$slug]["title"],
                "menu-item-object" => "page",
                "menu-item-object-id" => $page_ids[$slug],
                "menu-item-type"   => "post_type",
                "menu-item-status" => "publish",
                "menu-item-position" => $i
            ]);
        }
    }

    // Asignar menu
    $locations = get_theme_mod("nav_menu_locations") ?: [];
    $locs = get_registered_nav_menus();
    $primary_key = "primary";
    if (!isset($locs["primary"])) {
        $keys = array_keys($locs);
        if ($keys) $primary_key = $keys[0];
    }
    $locations[$primary_key] = $menu_id;
    set_theme_mod("nav_menu_locations", $locations);

    // Homepage estatica
    if (isset($page_ids["inicio"])) {
        update_option("show_on_front", "page");
        update_option("page_on_front", $page_ids["inicio"]);
    }

    // Logo
    $logo_path = WP_CONTENT_DIR . "/uploads/logos/river-logo.png";
    if (file_exists($logo_path)) {
        $existing_logo_id = get_theme_mod("custom_logo");
        if (!$existing_logo_id) {
            $attach_id = wp_insert_attachment([
                "guid"           => content_url("/uploads/logos/river-logo.png"),
                "post_mime_type" => "image/png",
                "post_title"     => "River Plate Logo",
                "post_status"    => "inherit"
            ], $logo_path);
            if (!is_wp_error($attach_id)) {
                $meta = wp_generate_attachment_metadata($attach_id, $logo_path);
                wp_update_attachment_metadata($attach_id, $meta);
                set_theme_mod("custom_logo", $attach_id);
            }
        }
    }

    update_option("wa_river_club_setup_done", true);
}

/* ================================================================
   CSS INTEGRAL — Club de Futbol Profesional
   ================================================================ */
add_action("wp_head", "river_css", 1);
function river_css() { ?>
<style id="wa-river-club-theme">
/* ============================================================
   RIVER PLATE INFO — Club de Futbol Profesional
   Paleta: Negro #111, Rojo #e63946, Blanco #fff, Gris #f5f5f5
   ============================================================ */

* { box-sizing:border-box; }
body {
    background:#f4f4f4 !important;
    color:#111 !important;
    font-family:"Segoe UI","Inter","Roboto",Arial,sans-serif !important;
    font-size:16px !important;
    line-height:1.7 !important;
    margin:0 !important;
}
img { max-width:100% !important; height:auto !important; }
a { color:#c62828 !important; text-decoration:none !important; }
a:hover { color:#e63946 !important; text-decoration:underline !important; }
.container,.container-fluid,.wrapper,.row { max-width:1200px !important; margin:0 auto !important; }

/* HEADER */
.mg-headwidget,header,.site-header {
    background:#111 !important;
    border-bottom:4px solid #e63946 !important;
    padding:24px 0 16px !important;
    text-align:center !important;
    position:relative !important;
}
.mg-headwidget:before,header:before {
    content:"" !important; display:block !important;
    width:60px !important; height:4px !important;
    background:#e63946 !important; margin:0 auto 12px !important; border-radius:2px !important;
}
.mg-headwidget:after,header:after {
    content:"\1F3C6 \1F3C6 \1F3C6   \2B50\2B50\2B50\2B50\2B50   \1F3C6 \1F3C6 \1F3C6" !important;
    display:block !important; font-size:14px !important; letter-spacing:3px !important;
    margin-top:8px !important; opacity:.9 !important;
}
.mg-headwidget .site-title a,.site-title a,.navbar-brand a,.mg-headwidget h1 a,.mg-headwidget h1 {
    color:#fff !important; font-weight:900 !important; font-size:28px !important;
    text-transform:uppercase !important; letter-spacing:-1px !important; text-decoration:none !important;
}
.site-description,.mg-headwidget .site-description,.tagline { color:#aaa !important; font-size:13px !important; margin-top:4px !important; }
.custom-logo,.site-logo img,.navbar-brand img { max-height:55px !important; filter:brightness(1.1) !important; }
.mg-head-detail { background:#000 !important; color:#888 !important; font-size:11px !important; padding:6px 0 !important; }
.mg-head-detail a { color:#e63946 !important; }

/* NAV */
.mg-nav-widget-area-back,.mg-menu-full,.navbar,.navbar-wp,.nav {
    background:#fff !important; border-bottom:1px solid #e0e0e0 !important;
}
.nav-link,.navbar-nav a,.nav a,.menu-item a {
    color:#111 !important; font-weight:700 !important; font-size:13px !important;
    text-transform:uppercase !important; letter-spacing:.5px !important;
    padding:14px 18px !important; display:inline-block !important; transition:all .15s !important;
}
.nav-link:hover,.navbar-nav a:hover,.nav a:hover,.menu-item a:hover,
.current-menu-item a,.nav-item.active .nav-link {
    color:#e63946 !important; background:#fafafa !important; text-decoration:none !important;
}

/* HERO */
.river-hero,.wp-block-cover.river-hero {
    background:#1a1a1a !important; border-radius:10px !important; margin-bottom:32px !important;
    position:relative !important; overflow:hidden !important;
}
.river-hero:before {
    content:"" !important; position:absolute !important; top:0;left:0;right:0;bottom:0 !important;
    background:linear-gradient(135deg,rgba(230,57,70,.15) 0%,transparent 50%,rgba(17,17,17,.4) 100%) !important;
    z-index:1 !important; pointer-events:none !important;
}
.river-hero .wp-block-cover__inner-container { position:relative !important; z-index:2 !important; }
.river-hero h1 { text-shadow:0 2px 12px rgba(0,0,0,.8) !important; }
.river-hero:after {
    content:"\1F3DF  EL MONUMENTAL" !important; position:absolute !important;
    bottom:20px !important; right:30px !important; color:rgba(255,255,255,.6) !important;
    font-size:13px !important; z-index:2 !important; letter-spacing:2px !important;
}

/* SECTION TITLES */
.river-section-title,.mg-sec-title,.mg-wid-title,.section-title,.widget-title,
.wp-block-heading.river-section-title {
    border-left:4px solid #e63946 !important; padding:6px 0 6px 14px !important; margin:32px 0 18px !important;
}
.river-section-title,.mg-sec-title h4,.mg-wid-title h4,.section-title h4,.widget-title,.wtitle {
    color:#111 !important; font-weight:800 !important; font-size:15px !important;
    text-transform:uppercase !important; letter-spacing:.5px !important; margin:0 !important;
}

/* CARDS */
.mg-blog-post,.mg-blog-post-3,.small-post,.mg-posts-sec-post,.post,article,.bs-post {
    background:#fff !important; border:1px solid #e8e8e8 !important; border-radius:8px !important;
    overflow:hidden !important; margin-bottom:20px !important; transition:transform .15s,box-shadow .15s !important;
    padding:0 !important;
}
.mg-blog-post:hover,.small-post:hover,.post:hover,article:hover {
    transform:translateY(-2px) !important; box-shadow:0 4px 16px rgba(0,0,0,.08) !important;
    border-color:#e63946 !important;
}
.mg-post-thumb img,.post-thumbnail img,.featured-image img,.back-img,.img-small-post {
    width:100% !important; height:210px !important; object-fit:cover !important;
    display:block !important; border-bottom:3px solid #e63946 !important;
}
.mg-content,.post-content-inner,.entry-content-wrap { padding:18px 20px !important; }
.mg-blog-category a,.newsup-categories a,.cat-links a,.post-category a,.category a {
    background:#e63946 !important; color:#fff !important; padding:4px 10px !important;
    border-radius:3px !important; font-size:11px !important; font-weight:700 !important;
    text-transform:uppercase !important; display:inline-block !important; letter-spacing:.5px !important;
}
.entry-title,.entry-title a,.title,.title a,.post-title,.post-title a,
h3.title,.title_small_post a,.mg-content h3 a {
    color:#111 !important; font-weight:800 !important; font-size:19px !important;
    line-height:1.35 !important; margin:10px 0 6px !important; display:block !important;
}
.entry-title a:hover,.title a:hover,.post-title a:hover { color:#c62828 !important; text-decoration:none !important; }
.title_small_post,.title_small_post a { font-size:15px !important; }
.mg-blog-date,.post-date,.entry-date,time,.post-meta { color:#888 !important; font-size:12px !important; }
.mg-content p,.post-excerpt p,.entry-content p { color:#444 !important; font-size:14px !important; line-height:1.6 !important; }

/* SPORTSPRESS */
.sp-template { background:#fff !important; border:1px solid #e8e8e8 !important; border-radius:8px !important; overflow:hidden !important; margin-bottom:24px !important; padding:0 !important; }
.sp-table-wrapper { overflow-x:auto !important; }
.sp-data-table,.sp-league-table { width:100% !important; border-collapse:collapse !important; font-size:14px !important; }
.sp-data-table thead th,.sp-league-table thead th {
    background:#111 !important; color:#fff !important; padding:12px 14px !important;
    font-weight:700 !important; font-size:12px !important; text-transform:uppercase !important;
    letter-spacing:.5px !important; border:none !important; text-align:left !important;
}
.sp-data-table tbody td,.sp-league-table tbody td {
    padding:10px 14px !important; border-bottom:1px solid #f0f0f0 !important; color:#333 !important;
}
.sp-data-table tbody tr:hover td,.sp-league-table tbody tr:hover td { background:#fafafa !important; }
.sp-data-table tbody tr:nth-child(even) td { background:#f9f9f9 !important; }
.sp-row-number { color:#aaa !important; }
.sp-highlight,.sp-data-table .data-name a { color:#111 !important; font-weight:700 !important; }

.sp-player-list .sp-player-number {
    background:#e63946 !important; color:#fff !important; width:32px !important; height:32px !important;
    border-radius:50% !important; display:flex !important; align-items:center !important;
    justify-content:center !important; font-weight:900 !important; font-size:14px !important; flex-shrink:0 !important;
}

.sp-event-blocks { display:flex !important; gap:20px !important; flex-wrap:wrap !important; }
.sp-event {
    background:#fff !important; border:2px solid #e8e8e8 !important; border-radius:10px !important;
    padding:20px !important; text-align:center !important; min-width:200px !important; flex:1 !important;
}
.sp-event:hover { border-color:#e63946 !important; }
.sp-event .sp-event-results,.sp-event .sp-event-score { font-size:28px !important; font-weight:900 !important; color:#e63946 !important; margin:10px 0 !important; }
.sp-event .sp-event-date,.sp-event .sp-event-time,.sp-event .sp-event-venue { color:#888 !important; font-size:12px !important; }

/* SIDEBAR */
.mg-sidebar .mg-widget,.widget,aside .widget {
    background:#fff !important; border:1px solid #e8e8e8 !important; border-radius:8px !important;
    padding:20px !important; margin-bottom:20px !important;
}
.mg-widget ul,.widget ul { list-style:none !important; padding:0 !important; margin:0 !important; }
.mg-widget li,.widget li { padding:10px 0 !important; border-bottom:1px solid #f0f0f0 !important; font-size:14px !important; }
.mg-widget li a,.widget li a { color:#333 !important; }
.mg-widget li a:hover { color:#e63946 !important; text-decoration:none !important; }
.widget_search input[type="search"],.search-form input {
    width:100% !important; padding:10px 14px !important; border:2px solid #e0e0e0 !important;
    border-radius:6px !important; font-size:14px !important; font-family:inherit !important;
}
.widget_search button,.search-form button {
    background:#111 !important; color:#fff !important; border:none !important;
    padding:10px 20px !important; border-radius:6px !important; font-weight:700 !important;
    cursor:pointer !important; margin-top:6px !important;
}

/* SINGLE POST */
.single .entry-title,.single .post-title {
    font-size:34px !important; font-weight:900 !important; line-height:1.2 !important;
    color:#111 !important; margin:28px 0 12px !important; padding:0 !important;
}
.single .entry-content,.single .post-content { font-size:17px !important; line-height:1.85 !important; color:#222 !important; }
.single .entry-content p,.single .post-content p { margin-bottom:18px !important; }
.single .entry-content h2,.single .post-content h2 {
    color:#111 !important; border-left:4px solid #e63946 !important;
    padding-left:16px !important; margin:36px 0 16px !important; font-size:22px !important; font-weight:800 !important;
}
.single .entry-content h3,.single .post-content h3 { color:#333 !important; font-size:18px !important; font-weight:700 !important; margin:28px 0 12px !important; }
.single .entry-content a,.single .post-content a { color:#c62828 !important; text-decoration:underline !important; }
.single .wp-block-post-featured-image img,.single .post-thumbnail img {
    width:100% !important; max-height:420px !important; object-fit:cover !important;
    border-radius:8px !important; border-bottom:3px solid #e63946 !important;
}

/* NEWSLETTER */
.newsletter,.subscribe-widget,form:has(input[type="email"]) {
    background:#111 !important; color:#fff !important; border-radius:10px !important;
    padding:28px !important; text-align:center !important; margin:20px 0 !important;
    border-top:3px solid #e63946 !important;
}
.newsletter h3,.subscribe-widget h3 { color:#fff !important; font-size:17px !important; margin:0 0 8px !important; }
.newsletter p,.subscribe-widget p { color:#aaa !important; font-size:13px !important; }
.newsletter input[type="email"],.subscribe-widget input[type="email"] {
    padding:14px !important; border:none !important; border-radius:6px !important;
    font-size:14px !important; width:100% !important; margin:10px 0 !important;
    background:#222 !important; color:#fff !important;
}
.newsletter button,.subscribe-widget button,input[type="submit"] {
    background:#e63946 !important; color:#fff !important; border:none !important;
    padding:14px 32px !important; border-radius:6px !important; font-weight:800 !important;
    text-transform:uppercase !important; cursor:pointer !important; letter-spacing:1px !important; width:100% !important;
}
.newsletter button:hover,.subscribe-widget button:hover { background:#c62828 !important; }

/* FOOTER */
footer,.mg-footer,.site-footer,.mg-footer-widget-area,.mg-footer-bottom-area {
    background:#111 !important; color:#aaa !important; padding:40px 20px !important;
    text-align:center !important; border-top:4px solid #e63946 !important;
}
.mg-footer-copyright {
    background:#000 !important; color:#888 !important; padding:28px 20px !important;
    text-align:center !important; border-top:1px solid #222 !important;
}
.mg-footer-copyright:before {
    content:"\1F3C6  EL MAS GRANDE  \1F3C6" !important; display:block !important;
    color:#e63946 !important; font-size:18px !important; letter-spacing:4px !important;
    margin-bottom:10px !important; font-weight:700 !important;
}
footer a,.mg-footer a { color:#e63946 !important; }
footer a:hover { color:#fff !important; }

/* PAGINATION */
.pagination,.navigation.pagination,.nav-links {
    display:flex !important; justify-content:center !important; gap:6px !important; padding:28px 0 !important;
}
.pagination .page-numbers,.nav-links a,.nav-links span {
    background:#fff !important; color:#111 !important; padding:10px 16px !important;
    border-radius:6px !important; border:1px solid #ddd !important; font-weight:700 !important;
    font-size:14px !important; display:inline-block !important; text-decoration:none !important;
}
.pagination .current,.nav-links .current { background:#111 !important; color:#fff !important; border-color:#111 !important; }
.pagination a:hover { background:#e63946 !important; color:#fff !important; border-color:#e63946 !important; text-decoration:none !important; }

/* TAG CLOUD */
.tagcloud a {
    background:#f0f0f0 !important; color:#111 !important; padding:6px 14px !important;
    border-radius:20px !important; font-size:12px !important; font-weight:600 !important;
    display:inline-block !important; margin:3px !important; transition:all .15s !important; text-decoration:none !important;
}
.tagcloud a:hover { background:#e63946 !important; color:#fff !important; }

/* TICKER */
.mg-latest-news {
    background:#fff !important; border:1px solid #e0e0e0 !important; border-radius:6px !important;
    padding:10px 16px !important; margin:18px 0 !important; font-size:13px !important;
}
.mg-latest-news a { color:#111 !important; font-weight:600 !important; }
.mg-latest-news a:hover { color:#e63946 !important; text-decoration:none !important; }

/* BUTTONS */
.btn,button:not(.nav-link),input[type="submit"] {
    background:#e63946 !important; color:#fff !important; border:none !important;
    padding:10px 20px !important; border-radius:6px !important; font-weight:700 !important;
    cursor:pointer !important; font-size:14px !important; transition:all .15s !important;
}
.btn:hover,button:not(.nav-link):hover,input[type="submit"]:hover { background:#111 !important; }

/* WOOCOMMERCE */
.woocommerce ul.products li.product {
    background:#fff !important; border:1px solid #e8e8e8 !important; border-radius:8px !important;
    padding:16px !important; transition:all .15s !important;
}
.woocommerce ul.products li.product:hover { border-color:#e63946 !important; box-shadow:0 4px 16px rgba(0,0,0,.08) !important; }
.woocommerce .button,.woocommerce a.button,.woocommerce button.button {
    background:#111 !important; color:#fff !important; border-radius:6px !important;
    font-weight:700 !important; padding:12px 24px !important; transition:all .15s !important;
}
.woocommerce .button:hover { background:#e63946 !important; }
.woocommerce span.onsale { background:#e63946 !important; border-radius:4px !important; }
.woocommerce div.product .product_title { color:#111 !important; font-weight:800 !important; }
.woocommerce div.product .price { color:#e63946 !important; font-weight:900 !important; }

/* RESPONSIVE */
@media (max-width:992px) {
    .col-md-4,.sidebar,.mg-sidebar,aside { flex:1 1 100% !important; }
    .sp-event-blocks { flex-direction:column !important; }
}
@media (max-width:768px) {
    .mg-headwidget .site-title a,.site-title a { font-size:22px !important; }
    .single .entry-title { font-size:24px !important; }
    .row,.mg-posts-sec-inner { padding:16px !important; }
    .mg-blog-post img,.post-thumbnail img { height:180px !important; }
    .river-hero h1 { font-size:28px !important; }
    .sp-data-table { font-size:12px !important; }
}
</style>
<?php }