with open('E:/DelMonte/web-analyzer/analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: H1 dedup
old_h1 = (
    '5c. Si no hay H1, agregarlo (oculto visualmente, visible para SEO)\n'
    "    if (!preg_match('/<h1[\\s>]/i', $html)) {{\n"
    "        $site_name = get_bloginfo('name');\n"
    "        $h1_tag = '<h1 style=\"position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0\">' . esc_html($site_name) . '</h1>';\n"
    '        $html = preg_replace(\'/<body[^>]*>/i\', \'$0\' . "\\n" . $h1_tag, $html, 1);\n'
    '    }}\n'
    '    // 5d. Lazy loading en todas las im'
)

new_h1 = (
    '5c. Asegurar exactamente 1 H1 (ni 0, ni 2+)\n'
    "    if (!preg_match('/<h1[\\s>]/i', $html)) {{\n"
    "        $site_name = get_bloginfo('name');\n"
    "        $h1_tag = '<h1 style=\"position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0\">' . esc_html($site_name) . '</h1>';\n"
    '        $html = preg_replace(\'/<body[^>]*>/i\', \'$0\' . "\\n" . $h1_tag, $html, 1);\n'
    '    }} elseif (preg_match_all(\'/<h1[\\s>]/i\', $html, $m) > 1) {{\n'
    '        // Hay multiples H1: conservar primero, convertir extras a h2\n'
    '        $seen = false;\n'
    "        $html = preg_replace_callback('/<h1([\\s>])/i', function($m) use (&$seen) {{\n"
    '            if (!$seen) {{ $seen = true; return $m[0]; }}\n'
    "            return '<h2' . $m[1];\n"
    '        }}, $html);\n'
    "        $html = preg_replace_callback('/<\\/h1>/i', function($m) use (&$seen) {{\n"
    '            static $count = 0; $count++;\n'
    '            if ($count <= 1) {{ return $m[0]; }}\n'
    "            return '</h2>';\n"
    '        }}, $html);\n'
    '    }}\n'
    '    // 5d. Lazy loading en todas las im'
)

if old_h1 in content:
    content = content.replace(old_h1, new_h1)
    print('OK: H1 dedup applied')
else:
    print('ERROR: H1 pattern not found')
    idx = content.find('5c. Si no hay H1')
    if idx >= 0:
        print('Found at', idx, ':', repr(content[idx:idx+200]))

# Fix 2: og:image fallback
old_og = (
    "    }} elseif (has_site_icon()) {{\n"
    "        echo '<meta property=\"og:image\" content=\"' . esc_url(get_site_icon_url(512)) . '\">' . \"\\\\n\";\n"
    '    }}\n'
)

new_og = (
    "    }} elseif (has_site_icon()) {{\n"
    "        echo '<meta property=\"og:image\" content=\"' . esc_url(get_site_icon_url(512)) . '\">' . \"\\\\n\";\n"
    '    }} else {{\n'
    '        // Fallback: primera imagen del contenido de la home\n'
    "        $front_id = get_option('page_on_front');\n"
    "        $front_content = $front_id ? get_post_field('post_content', $front_id) : '';\n"
    "        if ($front_content && preg_match('/<img[^>]+src=[\"\\\\']([^\"\\\\'>]+)/i', $front_content, $img_m)) {{\n"
    "            echo '<meta property=\"og:image\" content=\"' . esc_url($img_m[1]) . '\">' . \"\\\\n\";\n"
    '        }} else {{\n'
    "            $default_logo = get_theme_mod('custom_logo') ? wp_get_attachment_image_src(get_theme_mod('custom_logo'), 'full') : null;\n"
    '            if ($default_logo) {{\n'
    "                echo '<meta property=\"og:image\" content=\"' . esc_url($default_logo[0]) . '\">' . \"\\\\n\";\n"
    '            }}\n'
    '        }}\n'
    '    }}\n'
)

if old_og in content:
    content = content.replace(old_og, new_og)
    print('OK: og:image fallback applied')
else:
    print('ERROR: og:image pattern not found')
    idx = content.find('has_site_icon()')
    if idx >= 0:
        print('Found at', idx, ':', repr(content[idx:idx+250]))

with open('E:/DelMonte/web-analyzer/analyzer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done.')
