<?php
/**
 * Theme functions and definitions
 *
 * @package NewsTack
 */
if ( ! function_exists( 'newstack_enqueue_styles' ) ) :
	/**
	 * @since 0.1
	 */
	function newstack_enqueue_styles() {
		wp_enqueue_style( 'newsup-style-parent', get_template_directory_uri() . '/style.css' );
		wp_enqueue_style( 'newstack-style', get_stylesheet_directory_uri() . '/style.css', array( 'newsup-style-parent' ), '1.0' );
		wp_enqueue_style('bootstrap', get_template_directory_uri() . '/css/bootstrap.css');
		wp_enqueue_style( 'newstack-default-css', get_stylesheet_directory_uri()."/css/colors/default.css" );

		wp_dequeue_style( 'newsup-default' );

		if(is_rtl()){
			wp_enqueue_style( 'newsup_style_rtl', trailingslashit( get_template_directory_uri() ) . 'style-rtl.css' );
	    }
		
	}

endif;
add_action( 'wp_enqueue_scripts', 'newstack_enqueue_styles', 9999 );

function newstack_theme_setup() {

	// Add default posts and comments RSS feed links to head.
	add_theme_support( 'automatic-feed-links' );

	/*
	 * Let WordPress manage the document title.
	 * By adding theme support, we declare that this theme does not use a
	 * hard-coded <title> tag in the document head, and expect WordPress to
	 * provide it for us.
	 */
	add_theme_support( 'title-tag' );

	//Load text domain for translation-ready
	load_theme_textdomain('newstack', get_stylesheet_directory() . '/languages');

	require( get_stylesheet_directory() . '/hooks/hooks.php' );
	require( get_stylesheet_directory() . '/hooks/hook-header-section.php' );
	require( get_stylesheet_directory() . '/customizer-default.php' );
	require( get_stylesheet_directory() . '/frontpage-options.php' );
	require( get_stylesheet_directory() . '/font.php' );


	// custom header Support
		$args = array(
			'default-image'		=>  get_stylesheet_directory_uri() .'/images/head-back.jpg',
			'width'			=> '1600',
			'height'		=> '600',
			'flex-height'		=> false,
			'flex-width'		=> false,
			'header-text'		=> true,
			'default-text-color'	=> '#143745'
		);
		add_theme_support( 'custom-header', $args );


		// This theme uses wp_nav_menu() in one location.
		register_nav_menus( array(
			'top_right' => __( 'Top Header menu', 'newstack' ),
		) );
		$args = array(
			'default-color' => '#EEEEF5',
			'default-image' => '',
		);
	add_theme_support( 'custom-background', $args );
} 
add_action( 'after_setup_theme', 'newstack_theme_setup' );

/**
 * Register widget area.
 *
 * @link https://developer.wordpress.org/themes/functionality/sidebars/#registering-a-sidebar
 */
function newstack_widgets_init() {
	
	register_sidebar( array(
		'name'          => esc_html__( 'Front-Page Left Sidebar Section', 'newstack'),
		'id'            => 'front-left-page-sidebar',
		'description'   => '',
		'before_widget' => '<div id="%1$s" class="mg-widget %2$s">',
		'after_widget'  => '</div>',
		'before_title'  => '<div class="mg-wid-title"><h6 class="wtitle">',
		'after_title'   => '</h6></div>',
	) );

	register_sidebar( array(
		'name'          => esc_html__( 'Front-Page Right Sidebar Section', 'newstack'),
		'id'            => 'front-right-page-sidebar',
		'description'   => '',
		'before_widget' => '<div id="%1$s" class="mg-widget %2$s">',
		'after_widget'  => '</div>',
		'before_title'  => '<div class="mg-wid-title"><h6 class="wtitle">',
		'after_title'   => '</h6></div>',
	) );

}
add_action( 'widgets_init', 'newstack_widgets_init' );


function newstack_remove_some_widgets(){
	// Unregister Frontpage sidebar
	unregister_sidebar( 'front-page-sidebar' );
}
add_action( 'widgets_init', 'newstack_remove_some_widgets', 11 );

add_action( 'customize_register', 'newstack_customizer_rid_values', 1000 );
function newstack_customizer_rid_values($wp_customize) {
  
  $wp_customize->get_setting('newsup_header_overlay_color')->default = 'rgba(10, 0, 0, 0.58)'; 
}