"""Patch the plugin generator: H1 dedup + og:image fallback."""
import re

filepath = 'E:/DelMonte/web-analyzer/analyzer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# ============================================================
# Fix 1: Replace "add H1 if missing" with "ensure exactly 1 H1"
# ============================================================
# Line ~1040: "5c. Si no hay H1" -> replace logic
for i, line in enumerate(lines):
    if '5c. Si no hay H1' in line:
        # Replace the comment
        lines[i] = line.replace(
            '5c. Si no hay H1, agregarlo (oculto visualmente, visible para SEO)',
            '5c. Asegurar exactamente 1 H1 (ni 0, ni 2+)'
        )
        print(f'Line {i+1}: comment updated')

    if i > 0 and 'preg_match_all' not in lines[i] and 'if (!preg_match' in line and 'h1' in line.lower():
        # This is the start of the H1 block. We need to add the elseif after the closing }}
        # Find the }} that closes this if block
        j = i
        while j < len(lines):
            if lines[j].strip() == '}}' and 'h1' in lines[j-1].lower():
                # Replace the closing }} and next line (5d comment) with our extended logic
                old_block = ''.join(lines[i:j+2])  # +2 to include 5d comment
                break
            j += 1
        else:
            print('WARN: could not find end of H1 block')
            continue

        # Build the new block
        indent = '    '
        new_block = f'''{lines[i].rstrip()}
{indent}    $site_name = get_bloginfo('name');
{indent}    $h1_tag = '<h1 style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0">' . esc_html($site_name) . '</h1>';
{indent}    $html = preg_replace('/<body[^>]*>/i', '$0' . "\\n" . $h1_tag, $html, 1);
{indent}}}}} elseif (preg_match_all('/<h1[\s>]/i', $html, $m) > 1) {{{{
{indent}    // Hay multiples H1: conservar primero, convertir extras a h2
{indent}    $seen = false;
{indent}    $html = preg_replace_callback('/<h1([\s>])/i', function($m) use (&$seen) {{{{
{indent}        if (!$seen) {{{{ $seen = true; return $m[0]; }}}}
{indent}        return '<h2' . $m[1];
{indent}    }}}}, $html);
{indent}    $html = preg_replace_callback('/<\\/h1>/i', function($m) use (&$seen) {{{{
{indent}        static $count = 0; $count++;
{indent}        if ($count <= 1) {{{{ return $m[0]; }}}}
{indent}        return '</h2>';
{indent}    }}}}, $html);
{indent}}}}}
{lines[j+1].rstrip()}
'''
        # Replace the old lines
        lines[i:j+2] = [new_block]
        print(f'Line {i+1}: H1 dedup logic added')
        break

# ============================================================
# Fix 2: og:image fallback
# ============================================================
for i, line in enumerate(lines):
    if 'has_site_icon())' in line and 'og:image' in lines[i-1]:
        # Find the closing }} of this elseif
        j = i
        while j < len(lines):
            if lines[j].strip() == '}}' and j > i+1:
                # Replace the last }} with extended logic
                indent = '        '
                new_else = f'''{indent}}}} else {{{{
{indent}    // Fallback: primera imagen del contenido de la home
{indent}    $front_id = get_option('page_on_front');
{indent}    $front_content = $front_id ? get_post_field('post_content', $front_id) : '';
{indent}    if ($front_content && preg_match('/<img[^>]+src=["\\\']([^"\\\'>]+)/i', $front_content, $img_m)) {{{{
{indent}        echo '<meta property="og:image" content="' . esc_url($img_m[1]) . '">' . "\\n";
{indent}    }}}} else {{{{
{indent}        $default_logo = get_theme_mod('custom_logo') ? wp_get_attachment_image_src(get_theme_mod('custom_logo'), 'full') : null;
{indent}        if ($default_logo) {{{{
{indent}            echo '<meta property="og:image" content="' . esc_url($default_logo[0]) . '">' . "\\n";
{indent}        }}}}
{indent}    }}}}
{indent}}}}}'''
                lines[j] = lines[j].replace('}}', new_else)
                print(f'Line {j+1}: og:image fallback added')
                break
        break

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Done. File updated.')
