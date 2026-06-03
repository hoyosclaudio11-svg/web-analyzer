<?php
/**
 * River Plate Info — Tema Oscuro
 * Skin CSS + Disclaimer Legal + Anti-Spam
 */
if (!defined("ABSPATH")) exit;

// ============================================================
// BARRA DE DISCLAIMER LEGAL — Inyectada en cada pagina
// ============================================================
add_action("wp_body_open", "river_disclaimer_bar", 1);
function river_disclaimer_bar() { ?>
<div id="river-disclaimer" style="
    background:#000; color:#fff; text-align:center; padding:10px 16px;
    font-size:13px; font-weight:600; letter-spacing:.3px;
    border-bottom:2px solid #e63946; line-height:1.5;
    font-family:'Segoe UI','Inter','Roboto',Arial,sans-serif;
">
    &#9888;&#65039; <strong>SITIO NO OFICIAL</strong> — Independiente y sin vinculo con el Club Atletico River Plate.
    Creado por hinchas. No afiliado al club. &nbsp;
    <a href="/aviso-legal" style="color:#e63946;text-decoration:underline;font-weight:700;">Mas informacion</a>
</div>
<?php }

// ============================================================
// ANTI-SPAM
// ============================================================
add_filter("pre_comment_approved", function($approved, $commentdata) {
    $blocked = ["seo","marketing","backlink","guest post","buy now","casino","viagra","cialis","essay","dissertation","crypto","nft","slot","poker","bet","loan","payday","lose weight","diet pill","work from home","earn money","make money","click here","free download","watch free","streaming"];
    $content = strtolower($commentdata["comment_content"] . " " . $commentdata["comment_author"] . " " . $commentdata["comment_author_url"]);
    foreach ($blocked as $word) {
        if (strpos($content, $word) !== false) return "spam";
    }
    return $approved;
}, 10, 2);

add_filter("pre_comment_approved", function($approved, $commentdata) {
    if (substr_count($commentdata["comment_content"], "http") > 2) return "spam";
    return $approved;
}, 20, 2);

add_action("wp_head", "river_css", 99999);
function river_css() { ?>
<style id="wa-river-club-theme">
/* ============================================================
   RIVER PLATE INFO — Tema Oscuro
   Paleta: Fondo #111, Cards #1e1e1e, Texto #ddd, Rojo #e63946
   Solo colores y fondos. No se toca grid/layout.
   ============================================================ */

/* === BASE === */
/* === RESET COMPLETO — Todo oscuro === */
/* wp-custom-css fuerza #page blanco con !important. Misma especificidad para ganar. */
html, body,
#page, .site-content,
.wrapper, .wrapper-inner,
.site, .site-wrapper,
article, .post, .page,
.mg-card-box, .mg-blog-post-box,
.missed-inner, .mg-latest-news-sec,
.mg-info-author-block, .mg-breadcrumb-section .overlay,
.mg-featured-slider, .mg-subscriber .overlay,
.container-fluid, .container,
.row, [class*="col-"] {
    background:#111 !important;
    background-color:#111 !important;
}
body {
    color:#ddd !important;
    font-family:"Segoe UI","Inter","Roboto",Arial,sans-serif !important;
    font-size:16px !important;
    line-height:1.6 !important;
}
a { color:#e63946 !important; text-decoration:none !important; }
a:hover { color:#ff6b6b !important; text-decoration:underline !important; }

/* DISCLAIMER BAR */
#river-disclaimer {
    position:sticky !important; top:0 !important; z-index:9999 !important;
}

/* === HEADER === */
.mg-headwidget,header,.site-header {
    background:#0a0a0a !important;
    border-bottom:4px solid #e63946 !important;
    padding:16px 0 12px !important;
    text-align:center !important;
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
.site-description,.mg-headwidget .site-description,.tagline { color:#888 !important; font-size:13px !important; margin-top:4px !important; }
.custom-logo,.site-logo img,.navbar-brand img { max-height:55px !important; filter:brightness(1.3) !important; }
.mg-head-detail { background:#000 !important; color:#777 !important; font-size:11px !important; padding:6px 0 !important; }
.mg-head-detail a { color:#e63946 !important; }

/* === NAV === */
.mg-nav-widget-area-back,.mg-menu-full,.navbar,.navbar-wp,.nav {
    background:#1a1a1a !important;
    border-bottom:1px solid #333 !important;
}
.nav-link,.navbar-nav a,.nav a,.menu-item a {
    color:#ccc !important; font-weight:700 !important; font-size:13px !important;
    text-transform:uppercase !important; letter-spacing:.5px !important;
    padding:14px 18px !important; transition:all .15s !important;
}
.nav-link:hover,.navbar-nav a:hover,.nav a:hover,.menu-item a:hover {
    color:#e63946 !important; background:#252525 !important; text-decoration:none !important;
}
.current-menu-item a,.nav-item.active .nav-link,.current-menu-item>a,.current_page_item a {
    color:#fff !important; background:#252525 !important; text-decoration:none !important;
    font-weight:900 !important;
}

/* === HERO === */
.river-hero,.wp-block-cover.river-hero {
    background:#0d0d0d !important; border-radius:10px !important; margin-bottom:20px !important;
    position:relative !important; overflow:hidden !important;
}
.river-hero:before {
    content:"" !important; position:absolute !important; top:0;left:0;right:0;bottom:0 !important;
    background:linear-gradient(135deg,rgba(230,57,70,.2) 0%,transparent 50%,rgba(0,0,0,.5) 100%) !important;
    z-index:1 !important; pointer-events:none !important;
}
.river-hero .wp-block-cover__inner-container { position:relative !important; z-index:2 !important; }
.river-hero h1 { text-shadow:0 2px 12px rgba(0,0,0,.9) !important; }
.river-hero:after {
    content:"\1F3DF  EL MONUMENTAL" !important; position:absolute !important;
    bottom:20px !important; right:30px !important; color:rgba(255,255,255,.4) !important;
    font-size:13px !important; z-index:2 !important; letter-spacing:2px !important;
}

/* === SECTION TITLES === */
.river-section-title,.mg-sec-title,.mg-wid-title,.section-title,.widget-title,
.wp-block-heading.river-section-title {
    border-left:4px solid #e63946 !important; padding:6px 0 6px 14px !important; margin:24px 0 12px !important;
}
.river-section-title,.mg-sec-title h4,.mg-wid-title h4,.section-title h4,.widget-title,.wtitle {
    color:#fff !important; font-weight:800 !important; font-size:15px !important;
    text-transform:uppercase !important; letter-spacing:.5px !important; margin:0 !important;
}

/* === CARDS / POSTS === */
.mg-blog-post,.mg-blog-post-3,.small-post,.mg-posts-sec-post,.post,article,.bs-post {
    background:#1e1e1e !important; border:1px solid #333 !important; border-radius:8px !important;
    overflow:hidden !important; margin-bottom:16px !important; transition:transform .15s,box-shadow .15s !important;
}
.mg-blog-post:hover,.small-post:hover,.post:hover,article:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 4px 20px rgba(230,57,70,.15) !important;
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
    color:#fff !important; font-weight:800 !important; font-size:19px !important;
    line-height:1.35 !important; margin:10px 0 6px !important; display:block !important;
}
.entry-title a:hover,.title a:hover,.post-title a:hover { color:#e63946 !important; text-decoration:none !important; }
.title_small_post,.title_small_post a { font-size:15px !important; }
.mg-blog-date,.post-date,.entry-date,time,.post-meta { color:#999 !important; font-size:12px !important; }
.mg-content p,.post-excerpt p,.entry-content p { color:#bbb !important; font-size:14px !important; line-height:1.6 !important; }

/* === FORZAR COLUMNAS EN BLOQUE DE NOTICIAS === */
.wp-block-latest-posts__list {
    display:grid !important; gap:16px !important; padding:0 !important; list-style:none !important;
}
.page-id-875 .wp-block-latest-posts__list { grid-template-columns:repeat(2, 1fr) !important; }
.page-id-866 .wp-block-latest-posts__list { grid-template-columns:repeat(3, 1fr) !important; }
.wp-block-latest-posts__list li {
    margin:0 !important; padding:0 !important; clear:none !important;
    float:none !important; width:auto !important; min-width:0 !important; overflow:hidden !important;
}
.wp-block-latest-posts__post-title {
    font-weight:800 !important; font-size:14px !important; line-height:1.3 !important; word-break:break-word !important;
    color:#fff !important;
}
.wp-block-latest-posts__post-title a { color:#fff !important; }
.wp-block-latest-posts__post-title a:hover { color:#e63946 !important; text-decoration:none !important; }
.wp-block-latest-posts__featured-image img {
    width:100% !important; height:160px !important; object-fit:cover !important;
    border-radius:6px !important; border-bottom:3px solid #e63946 !important;
}
.wp-block-latest-posts__post-date { font-size:11px !important; color:#999 !important; }
@media (max-width:768px) {
    .wp-block-latest-posts__list { grid-template-columns:1fr !important; }
}

/* === SPORTSPRESS === */
.sp-template {
    background:#1e1e1e !important; border:1px solid #333 !important;
    border-radius:8px !important; overflow:hidden !important; margin-bottom:16px !important;
}
.sp-table-wrapper { overflow-x:auto !important; }
.sp-data-table,.sp-league-table { width:100% !important; border-collapse:collapse !important; font-size:14px !important; color:#ccc !important; }
.sp-data-table thead th,.sp-league-table thead th {
    background:#0a0a0a !important; color:#fff !important; padding:12px 14px !important;
    font-weight:700 !important; font-size:12px !important; text-transform:uppercase !important;
    letter-spacing:.5px !important; border:none !important; text-align:left !important;
}
.sp-data-table tbody td,.sp-league-table tbody td {
    padding:10px 14px !important; border-bottom:1px solid #333 !important; color:#ccc !important;
}
.sp-data-table tbody tr:hover td,.sp-league-table tbody tr:hover td { background:#252525 !important; }
.sp-data-table tbody tr:nth-child(even) td { background:#1a1a1a !important; }
.sp-row-number { color:#666 !important; }
.sp-highlight,.sp-data-table .data-name a { color:#fff !important; font-weight:700 !important; }
.sp-player-list .sp-player-number {
    background:#e63946 !important; color:#fff !important; width:32px !important; height:32px !important;
    border-radius:50% !important; display:flex !important; align-items:center !important;
    justify-content:center !important; font-weight:900 !important; font-size:14px !important; flex-shrink:0 !important;
}
.sp-event-blocks { display:flex !important; gap:20px !important; flex-wrap:wrap !important; }
.sp-event {
    background:#1e1e1e !important; border:2px solid #333 !important; border-radius:10px !important;
    padding:20px !important; text-align:center !important; min-width:200px !important; flex:1 !important;
}
.sp-event:hover { border-color:#e63946 !important; }
.sp-event .sp-event-results,.sp-event .sp-event-score { font-size:28px !important; font-weight:900 !important; color:#e63946 !important; margin:10px 0 !important; }
.sp-event .sp-event-date,.sp-event .sp-event-time,.sp-event .sp-event-venue { color:#999 !important; font-size:12px !important; }

/* === SIDEBAR === */
.mg-sidebar .mg-widget,.widget,aside .widget {
    background:#1e1e1e !important; border:1px solid #333 !important;
    border-radius:8px !important; padding:20px !important; margin-bottom:20px !important;
}
.mg-widget ul,.widget ul { list-style:none !important; padding:0 !important; margin:0 !important; }
.mg-widget li,.widget li {
    padding:10px 0 !important; border-bottom:1px solid #333 !important; font-size:14px !important;
}
.mg-widget li a,.widget li a { color:#bbb !important; }
.mg-widget li a:hover { color:#e63946 !important; text-decoration:none !important; }
.widget_search input[type="search"],.search-form input {
    width:100% !important; padding:10px 14px !important;
    border:2px solid #444 !important; border-radius:6px !important;
    font-size:14px !important; font-family:inherit !important;
    background:#252525 !important; color:#ddd !important;
}
.widget_search button,.search-form button {
    background:#e63946 !important; color:#fff !important; border:none !important;
    padding:10px 20px !important; border-radius:6px !important; font-weight:700 !important;
    cursor:pointer !important; margin-top:6px !important;
}

/* === SINGLE POST === */
.single .entry-title,.single .post-title {
    font-size:34px !important; font-weight:900 !important; line-height:1.2 !important;
    color:#fff !important; margin:28px 0 12px !important; padding:0 !important;
}
.single .entry-content,.single .post-content { font-size:17px !important; line-height:1.85 !important; color:#ccc !important; }
.single .entry-content p,.single .post-content p { margin-bottom:18px !important; }
.single .entry-content h2,.single .post-content h2 {
    color:#fff !important; border-left:4px solid #e63946 !important;
    padding-left:16px !important; margin:36px 0 16px !important; font-size:22px !important; font-weight:800 !important;
}
.single .entry-content h3,.single .post-content h3 { color:#ddd !important; font-size:18px !important; font-weight:700 !important; margin:28px 0 12px !important; }
.single .entry-content a,.single .post-content a { color:#e63946 !important; text-decoration:underline !important; }
.single .wp-block-post-featured-image img,.single .post-thumbnail img {
    width:100% !important; max-height:420px !important; object-fit:cover !important;
    border-radius:8px !important; border-bottom:3px solid #e63946 !important;
}

/* === NEWSLETTER === */
.newsletter,.subscribe-widget,form:has(input[type="email"]) {
    background:#0a0a0a !important; color:#fff !important; border-radius:10px !important;
    padding:28px !important; text-align:center !important; margin:20px 0 !important;
    border-top:3px solid #e63946 !important;
}
.newsletter h3,.subscribe-widget h3 { color:#fff !important; font-size:17px !important; margin:0 0 8px !important; }
.newsletter p,.subscribe-widget p { color:#888 !important; font-size:13px !important; }
.newsletter input[type="email"],.subscribe-widget input[type="email"] {
    padding:14px !important; border:none !important; border-radius:6px !important;
    font-size:14px !important; width:100% !important; margin:10px 0 !important;
    background:#252525 !important; color:#fff !important;
}
.newsletter button,.subscribe-widget button,input[type="submit"] {
    background:#e63946 !important; color:#fff !important; border:none !important;
    padding:14px 32px !important; border-radius:6px !important; font-weight:800 !important;
    text-transform:uppercase !important; cursor:pointer !important; letter-spacing:1px !important; width:100% !important;
}
.newsletter button:hover,.subscribe-widget button:hover { background:#c62828 !important; }

/* === FOOTER === */
footer,.mg-footer,.site-footer,.mg-footer-widget-area,.mg-footer-bottom-area {
    background:#0a0a0a !important; color:#888 !important; padding:40px 20px !important;
    text-align:center !important; border-top:4px solid #e63946 !important;
}
.mg-footer-copyright {
    background:#000 !important; color:#777 !important; padding:28px 20px !important;
    text-align:center !important; border-top:1px solid #222 !important;
}
.mg-footer-copyright:before {
    content:"\1F3C6  EL MAS GRANDE  \1F3C6" !important; display:block !important;
    color:#e63946 !important; font-size:18px !important; letter-spacing:4px !important;
    margin-bottom:10px !important; font-weight:700 !important;
}
.mg-footer-copyright:after {
    content:"\A\A\26A0  SITIO NO OFICIAL. Independiente y sin vinculo con el Club Atletico River Plate. Creado por hinchas. Las marcas y logotipos pertenecen a sus respectivos titulares. Los enlaces a MercadoLibre son de afiliado." !important;
    display:block !important; color:#555 !important; font-size:11px !important;
    margin-top:12px !important; line-height:1.5 !important;
    white-space:pre-wrap !important;
}
footer a,.mg-footer a { color:#e63946 !important; }
footer a:hover { color:#fff !important; }

/* === PAGINATION === */
.pagination,.navigation.pagination,.nav-links {
    display:flex !important; justify-content:center !important; gap:6px !important; padding:28px 0 !important;
}
.pagination .page-numbers,.nav-links a,.nav-links span {
    background:#1e1e1e !important; color:#ccc !important; padding:10px 16px !important;
    border-radius:6px !important; border:1px solid #444 !important; font-weight:700 !important;
    font-size:14px !important; display:inline-block !important; text-decoration:none !important;
}
.pagination .current,.nav-links .current { background:#e63946 !important; color:#fff !important; border-color:#e63946 !important; }
.pagination a:hover { background:#e63946 !important; color:#fff !important; border-color:#e63946 !important; text-decoration:none !important; }

/* === TAG CLOUD === */
.tagcloud a {
    background:#333 !important; color:#ccc !important; padding:6px 14px !important;
    border-radius:20px !important; font-size:12px !important; font-weight:600 !important;
    display:inline-block !important; margin:3px !important; transition:all .15s !important; text-decoration:none !important;
}
.tagcloud a:hover { background:#e63946 !important; color:#fff !important; }

/* === TICKER === */
.mg-latest-news {
    background:#1e1e1e !important; border:1px solid #333 !important; border-radius:6px !important;
    padding:10px 16px !important; margin:18px 0 !important; font-size:13px !important;
}
.mg-latest-news a { color:#fff !important; font-weight:600 !important; }
.mg-latest-news a:hover { color:#e63946 !important; text-decoration:none !important; }

/* === BUTTONS === */
.btn,button:not(.nav-link),input[type="submit"] {
    background:#e63946 !important; color:#fff !important; border:none !important;
    padding:10px 20px !important; border-radius:6px !important; font-weight:700 !important;
    cursor:pointer !important; font-size:14px !important; transition:all .15s !important;
}
.btn:hover,button:not(.nav-link):hover,input[type="submit"]:hover { background:#c62828 !important; }

/* === AFILIADO BADGE === */
.papafpro-produto-card:before,
.papafpro-produto:before {
    content:"Enlace de Afiliado" !important;
    display:inline-block !important;
    background:#3d2e00 !important; color:#ffc107 !important;
    font-size:10px !important; font-weight:700 !important;
    padding:3px 8px !important; border-radius:3px !important;
    margin-bottom:6px !important; text-transform:uppercase !important;
    letter-spacing:.5px !important; border:1px solid #ffc107 !important;
}

/* === WOOCOMMERCE === */
.woocommerce ul.products li.product {
    background:#1e1e1e !important; border:1px solid #333 !important; border-radius:8px !important;
    padding:16px !important; transition:all .15s !important;
}
.woocommerce ul.products li.product:hover { border-color:#e63946 !important; box-shadow:0 4px 16px rgba(230,57,70,.15) !important; }
.woocommerce .button,.woocommerce a.button,.woocommerce button.button {
    background:#e63946 !important; color:#fff !important; border-radius:6px !important;
    font-weight:700 !important; padding:12px 24px !important; transition:all .15s !important;
}
.woocommerce .button:hover { background:#c62828 !important; }
.woocommerce span.onsale { background:#e63946 !important; border-radius:4px !important; }
.woocommerce div.product .product_title { color:#fff !important; font-weight:800 !important; }
.woocommerce div.product .price { color:#e63946 !important; font-weight:900 !important; }

/* === SOBREESCRIBIR FONDOS CLAROS DEL TEMA === */
/* WordPress blocks con background forzado */
.has-background,
.has-white-background-color,
.has-very-light-gray-background-color,
.has-pale-cyan-blue-background-color,
.has-vivid-cyan-blue-background-color,
.has-pale-pink-background-color,
.has-luminous-vivid-amber-background-color,
.has-luminous-vivid-orange-background-color,
.has-light-green-cyan-background-color,
[class*="has-"][class*="-background-color"] {
    background-color:#1e1e1e !important;
}
/* Newsup inner containers */
.mg-posts-sec-inner,
.mg-posts-modul,
.small-list-post,
.mg-blog-post-box,
.mg-posts-modul-6,
.mg-sec-inner,
.mg-card-body,
.bs-card-body,
.mg-posts-sec,
.mg-widget .mg-widget-body,
.wp-block-group.has-background,
.wp-block-cover__inner-container {
    background:#1e1e1e !important;
}
.mg-posts-sec-inner,
.mg-posts-modul,
.small-list-post,
.mg-sec-inner,
.mg-card-body,
.bs-card-body {
    color:#ddd !important;
}
.mg-posts-sec-inner a,
.mg-posts-modul a,
.small-list-post a,
.mg-sec-inner a,
.mg-card-body a {
    color:#e63946 !important;
}
.mg-posts-sec-inner h2,
.mg-posts-sec-inner h3,
.mg-posts-sec-inner h4,
.mg-posts-modul h2,
.mg-posts-modul h3,
.small-list-post h2,
.small-list-post h3,
.mg-sec-inner h2,
.mg-sec-inner h3 {
    color:#fff !important;
}
.mg-posts-sec-inner .mg-blog-post,
.mg-posts-modul .mg-blog-post {
    background:#252525 !important;
    border-color:#3a3a3a !important;
}
.mg-posts-sec-inner .mg-blog-date,
.small-list-post .mg-blog-date,
.mg-posts-modul .post-date,
.mg-posts-modul .post-meta {
    color:#888 !important;
}

/* === HIDE THEME CREDITS === */
.mg-footer-copyright p:last-child,
.site-info,.copyright,.mg-footer-copyright a[rel="designer"],
footer .container-fluid .row:last-child>div:last-child,
.mg-footer-bottom-area+.row { display:none !important; }

/* === HIDE DUPLICATE NEWSLETTER IN FOOTER === */
footer .newsletter,footer .subscribe-widget,
.mg-footer-widget-area .newsletter,
footer form:has(input[type="email"]):not(.search-form form) { display:none !important; }
.mg-footer-widget-area .newsletter+.newsletter,
footer form+form:has(input[type="email"]) { display:none !important; }

/* === FORCE LOGO DISPLAY === */
.custom-logo-link,.custom-logo { display:inline-block !important; max-width:80px !important; }
.site-logo img,.custom-logo-link img { max-height:60px !important; width:auto !important; }

/* === RESPONSIVE === */
@media (max-width:768px) {
    .mg-headwidget .site-title a,.site-title a { font-size:22px !important; }
    .single .entry-title { font-size:24px !important; }
    .mg-blog-post img,.post-thumbnail img { height:180px !important; }
    .river-hero h1 { font-size:28px !important; }
    .sp-data-table { font-size:12px !important; }
    #river-disclaimer { font-size:11px !important; padding:8px 10px !important; }
}
</style>
<?php }