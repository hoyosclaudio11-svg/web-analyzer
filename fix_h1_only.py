with open('E:/DelMonte/web-analyzer/analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if old_h1 substring exists
idx = content.find('5c. Si no hay H1')
if idx < 0:
    print('H1 section not found at all')
    exit()

# Extract the exact text from the file to use as old_string
# Find end marker
end_idx = content.find('5d. Lazy loading', idx)
if end_idx < 0:
    print('End marker not found')
    exit()

# Extract exact old text including the 5d line prefix
old_text = content[idx:end_idx + len('5d. Lazy loading en todas las imagenes')]
print('Old text length:', len(old_text))

# Build new text
new_text = (
    '5c. Asegurar exactamente 1 H1 (ni 0, ni 2+)\n'
    "    if (!preg_match('/<h1[\\s>]/i', $html)) {{\n"
    "        $site_name = get_bloginfo('name');\n"
    '        $h1_tag = \'<h1 style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0">\' . esc_html($site_name) . \'</h1>\';\n'
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
    '    // 5d. Lazy loading en todas las imagenes'
)

content = content.replace(old_text, new_text)
with open('E:/DelMonte/web-analyzer/analyzer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK: H1 fix applied' if old_text != new_text else 'No change needed')
