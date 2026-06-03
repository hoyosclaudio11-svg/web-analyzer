<?php
/**
 * River Plate Info — Tema Limpio Profesional
 * Rojo + Negro + Blanco. Alta legibilidad.
 */
if (!defined("ABSPATH")) exit;

// Nuke CSS del tema que interfiere
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

add_action("wp_head", "river_css", 1);
function river_css() { ?>
<style id="wa-river-theme">
/* ============================================================
   RIVER PLATE INFO — Limpio, Legible, Futbolero
   Paleta: Negro #111, Rojo #e63946, Blanco #fff, Gris #f5f5f5
   ============================================================ */

/* === BASE — Maxima legibilidad === */
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

/* === CONTENEDOR === */
.container,.container-fluid,.wrapper,.row {
    max-width:1200px !important;
    margin:0 auto !important;
}

/* ============================================
   HEADER — Negro + Rojo
   ============================================ */
.mg-headwidget,header,.site-header {
    background:#111 !important;
    border-bottom:4px solid #e63946 !important;
    padding:24px 0 16px !important;
    text-align:center !important;
}
/* Banda roja decorativa */
.mg-headwidget:before,header:before {
    content:"" !important;
    display:block !important;
    width:60px !important;
    height:4px !important;
    background:#e63946 !important;
    margin:0 auto 12px !important;
    border-radius:2px !important;
}
/* Trofeos con estrellas */
.mg-headwidget:after {
    content:"\1F3C6 \1F3C6 \1F3C6   \2B50\2B50\2B50\2B50\2B50   \1F3C6 \1F3C6 \1F3C6" !important;
    display:block !important;
    font-size:14px !important;
    letter-spacing:3px !important;
    margin-top:8px !important;
    opacity:.9 !important;
}
.mg-headwidget .site-title a,.site-title a,.navbar-brand,.navbar-brand a,
.mg-headwidget h1 a,.mg-headwidget h1 {
    color:#fff !important;
    font-weight:900 !important;
    font-size:28px !important;
    text-transform:uppercase !important;
    letter-spacing:-1px !important;
    text-decoration:none !important;
}
.site-description,.mg-headwidget .site-description,.tagline {
    color:#aaa !important;
    font-size:13px !important;
    margin-top:4px !important;
}
/* Logo */
.custom-logo,.site-logo img,.navbar-brand img {
    max-height:55px !important;
    filter:brightness(1.1) !important;
}

/* Detalle superior (fecha/hora) */
.mg-head-detail {
    background:#000 !important;
    color:#888 !important;
    font-size:11px !important;
    padding:6px 0 !important;
}
.mg-head-detail a { color:#e63946 !important; }

/* ============================================
   NAVEGACION — Fondo blanco, texto negro
   ============================================ */
.mg-nav-widget-area-back,.mg-menu-full,.navbar,.navbar-wp,.nav {
    background:#fff !important;
    border-bottom:1px solid #e0e0e0 !important;
}
.nav-link,.navbar-nav a,.nav a,.menu-item a {
    color:#111 !important;
    font-weight:700 !important;
    font-size:13px !important;
    text-transform:uppercase !important;
    letter-spacing:.5px !important;
    padding:14px 18px !important;
    display:inline-block !important;
    transition:all .15s !important;
}
.nav-link:hover,.navbar-nav a:hover,.nav a:hover,.menu-item a:hover,
.current-menu-item a,.nav-item.active .nav-link {
    color:#e63946 !important;
    background:#fafafa !important;
    text-decoration:none !important;
}

/* ============================================
   LAYOUT PRINCIPAL
   ============================================ */
.row,.mg-posts-sec-inner,.content-area {
    display:flex !important;
    flex-wrap:wrap !important;
    gap:28px !important;
    padding:36px 0 !important;
}
.col-md-8,.content-area main,.site-main {
    flex:1 1 65% !important;
    min-width:0 !important;
    background:transparent !important;
}
.col-md-4,.sidebar,.mg-sidebar,aside {
    flex:0 0 330px !important;
    background:transparent !important;
}

/* ============================================
   CARDS DE NOTICIAS — Blanco puro, sombra suave
   ============================================ */
.mg-blog-post,.mg-blog-post-3,.small-post,.mg-posts-sec-post,
.post,article,.bs-post {
    background:#fff !important;
    border:1px solid #e8e8e8 !important;
    border-radius:8px !important;
    overflow:hidden !important;
    margin-bottom:20px !important;
    transition:transform .15s,box-shadow .15s !important;
    padding:0 !important;
}
.mg-blog-post:hover,.small-post:hover,.post:hover,article:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 4px 16px rgba(0,0,0,.08) !important;
    border-color:#e63946 !important;
}

/* Imagen */
.mg-post-thumb img,.post-thumbnail img,.featured-image img,.back-img,.img-small-post {
    width:100% !important;
    height:210px !important;
    object-fit:cover !important;
    display:block !important;
    border-bottom:3px solid #e63946 !important;
}

/* Contenido de la card */
.mg-content,.post-content-inner,.entry-content-wrap {
    padding:18px 20px !important;
}

/* Categoria badge */
.mg-blog-category a,.newsup-categories a,.cat-links a,.post-category a,.category a {
    background:#e63946 !important;
    color:#fff !important;
    padding:4px 10px !important;
    border-radius:3px !important;
    font-size:11px !important;
    font-weight:700 !important;
    text-transform:uppercase !important;
    display:inline-block !important;
    letter-spacing:.5px !important;
}

/* Titulo — NEGRO, GRANDE, LEGIBLE */
.entry-title,.entry-title a,.title,.title a,.post-title,.post-title a,
h3.title,.title_small_post a,.mg-content h3 a {
    color:#111 !important;
    font-weight:800 !important;
    font-size:19px !important;
    line-height:1.35 !important;
    margin:10px 0 6px !important;
    display:block !important;
}
.entry-title a:hover,.title a:hover,.post-title a:hover {
    color:#c62828 !important;
    text-decoration:none !important;
}
.title_small_post,.title_small_post a { font-size:15px !important; }

/* Fecha y meta */
.mg-blog-date,.post-date,.entry-date,time,.post-meta {
    color:#888 !important;
    font-size:12px !important;
}

/* Extracto */
.mg-content p,.post-excerpt p,.entry-content p {
    color:#444 !important;
    font-size:14px !important;
    line-height:1.6 !important;
}

/* ============================================
   TITULOS DE SECCION
   ============================================ */
.mg-sec-title,.mg-wid-title,.section-title,.widget-title {
    border-left:4px solid #e63946 !important;
    padding:6px 0 6px 14px !important;
    margin-bottom:18px !important;
}
.mg-sec-title h4,.mg-wid-title h4,.section-title h4,.widget-title,.wtitle {
    color:#111 !important;
    font-weight:800 !important;
    font-size:15px !important;
    text-transform:uppercase !important;
    letter-spacing:.5px !important;
    margin:0 !important;
}

/* ============================================
   SIDEBAR
   ============================================ */
.mg-sidebar .mg-widget,.widget,aside .widget {
    background:#fff !important;
    border:1px solid #e8e8e8 !important;
    border-radius:8px !important;
    padding:20px !important;
    margin-bottom:20px !important;
}
.mg-widget ul,.widget ul { list-style:none !important; padding:0 !important; margin:0 !important; }
.mg-widget li,.widget li {
    padding:10px 0 !important;
    border-bottom:1px solid #f0f0f0 !important;
    font-size:14px !important;
}
.mg-widget li a,.widget li a { color:#333 !important; }
.mg-widget li a:hover { color:#e63946 !important; text-decoration:none !important; }

/* Buscador */
.widget_search input[type="search"],.search-form input {
    width:100% !important;
    padding:10px 14px !important;
    border:2px solid #e0e0e0 !important;
    border-radius:6px !important;
    font-size:14px !important;
    font-family:inherit !important;
}
.widget_search button,.search-form button {
    background:#111 !important;
    color:#fff !important;
    border:none !important;
    padding:10px 20px !important;
    border-radius:6px !important;
    font-weight:700 !important;
    cursor:pointer !important;
    margin-top:6px !important;
}

/* ============================================
   SINGLE POST — Lectura comoda
   ============================================ */
.single .entry-title,.single .post-title {
    font-size:34px !important;
    font-weight:900 !important;
    line-height:1.2 !important;
    color:#111 !important;
    margin:28px 0 12px !important;
    padding:0 !important;
}
.single .entry-content,.single .post-content {
    font-size:17px !important;
    line-height:1.85 !important;
    color:#222 !important;
}
.single .entry-content p,.single .post-content p {
    margin-bottom:18px !important;
}
.single .entry-content h2,.single .post-content h2 {
    color:#111 !important;
    border-left:4px solid #e63946 !important;
    padding-left:16px !important;
    margin:36px 0 16px !important;
    font-size:22px !important;
    font-weight:800 !important;
}
.single .entry-content h3,.single .post-content h3 {
    color:#333 !important;
    font-size:18px !important;
    font-weight:700 !important;
    margin:28px 0 12px !important;
}
.single .entry-content a,.single .post-content a {
    color:#c62828 !important;
    text-decoration:underline !important;
}
/* Imagen destacada */
.single .wp-block-post-featured-image img,.single .post-thumbnail img {
    width:100% !important;
    max-height:420px !important;
    object-fit:cover !important;
    border-radius:8px !important;
    border-bottom:3px solid #e63946 !important;
}

/* ============================================
   NEWSLETTER
   ============================================ */
.newsletter,.subscribe-widget,form:has(input[type="email"]) {
    background:#111 !important;
    color:#fff !important;
    border-radius:10px !important;
    padding:28px !important;
    text-align:center !important;
    margin:20px 0 !important;
    border-top:3px solid #e63946 !important;
}
.newsletter h3,.subscribe-widget h3 {
    color:#fff !important;
    font-size:17px !important;
    margin:0 0 8px !important;
}
.newsletter p,.subscribe-widget p { color:#aaa !important; font-size:13px !important; }
.newsletter input[type="email"],.subscribe-widget input[type="email"] {
    padding:14px !important;
    border:none !important;
    border-radius:6px !important;
    font-size:14px !important;
    width:100% !important;
    margin:10px 0 !important;
    background:#222 !important;
    color:#fff !important;
}
.newsletter input[type="email"]::placeholder { color:#888 !important; }
.newsletter button,.subscribe-widget button,input[type="submit"] {
    background:#e63946 !important;
    color:#fff !important;
    border:none !important;
    padding:14px 32px !important;
    border-radius:6px !important;
    font-size:14px !important;
    font-weight:800 !important;
    text-transform:uppercase !important;
    cursor:pointer !important;
    letter-spacing:1px !important;
    width:100% !important;
}
.newsletter button:hover,.subscribe-widget button:hover {
    background:#c62828 !important;
}

/* ============================================
   FOOTER — Negro total
   ============================================ */
footer,.mg-footer,.site-footer,.mg-footer-widget-area,.mg-footer-bottom-area {
    background:#111 !important;
    color:#aaa !important;
    padding:40px 20px !important;
    text-align:center !important;
    border-top:4px solid #e63946 !important;
}
.mg-footer-copyright {
    background:#000 !important;
    color:#888 !important;
    padding:28px 20px !important;
    text-align:center !important;
    border-top:1px solid #222 !important;
}
/* Trofeos footer */
.mg-footer-copyright:before {
    content:"\1F3C6  EL MAS GRANDE  \1F3C6" !important;
    display:block !important;
    color:#e63946 !important;
    font-size:18px !important;
    letter-spacing:4px !important;
    margin-bottom:10px !important;
    font-weight:700 !important;
}
footer a,.mg-footer a { color:#e63946 !important; }
footer a:hover { color:#fff !important; }

/* ============================================
   PAGINACION
   ============================================ */
.pagination,.navigation.pagination,.nav-links {
    display:flex !important;
    justify-content:center !important;
    gap:6px !important;
    padding:28px 0 !important;
}
.pagination .page-numbers,.nav-links a,.nav-links span {
    background:#fff !important;
    color:#111 !important;
    padding:10px 16px !important;
    border-radius:6px !important;
    border:1px solid #ddd !important;
    font-weight:700 !important;
    font-size:14px !important;
    display:inline-block !important;
    text-decoration:none !important;
}
.pagination .current,.nav-links .current {
    background:#111 !important;
    color:#fff !important;
    border-color:#111 !important;
}
.pagination a:hover { background:#e63946 !important; color:#fff !important; border-color:#e63946 !important; text-decoration:none !important; }

/* ============================================
   TAG CLOUD
   ============================================ */
.tagcloud a {
    background:#f0f0f0 !important;
    color:#111 !important;
    padding:6px 14px !important;
    border-radius:20px !important;
    font-size:12px !important;
    font-weight:600 !important;
    display:inline-block !important;
    margin:3px !important;
    transition:all .15s !important;
    text-decoration:none !important;
}
.tagcloud a:hover {
    background:#e63946 !important;
    color:#fff !important;
}

/* ============================================
   ULTIMAS NOTICIAS (ticker)
   ============================================ */
.mg-latest-news {
    background:#fff !important;
    border:1px solid #e0e0e0 !important;
    border-radius:6px !important;
    padding:10px 16px !important;
    margin:18px 0 !important;
    font-size:13px !important;
}
.mg-latest-news a { color:#111 !important; font-weight:600 !important; }
.mg-latest-news a:hover { color:#e63946 !important; text-decoration:none !important; }

/* ============================================
   BOTONES GENERICOS
   ============================================ */
.btn,button:not(.nav-link),input[type="submit"] {
    background:#e63946 !important;
    color:#fff !important;
    border:none !important;
    padding:10px 20px !important;
    border-radius:6px !important;
    font-weight:700 !important;
    cursor:pointer !important;
    font-size:14px !important;
    transition:all .15s !important;
}
.btn:hover,button:not(.nav-link):hover,input[type="submit"]:hover {
    background:#111 !important;
}

/* ============================================
   RESPONSIVE
   ============================================ */
@media (max-width:992px) {
    .col-md-4,.sidebar,.mg-sidebar,aside { flex:1 1 100% !important; }
}
@media (max-width:768px) {
    .mg-headwidget .site-title a,.site-title a { font-size:22px !important; }
    .single .entry-title { font-size:24px !important; }
    .row,.mg-posts-sec-inner { padding:16px !important; }
    .mg-blog-post img,.post-thumbnail img { height:180px !important; }
}
</style>
<?php }