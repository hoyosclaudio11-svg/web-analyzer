with open('E:/DelMonte/web-analyzer/analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('5c. Si no hay H1')
snippet = content[idx:idx+350]

old_h1 = (
    '5c. Si no hay H1, agregarlo (oculto visualmente, visible para SEO)\n'
    "    if (!preg_match('/<h1[\\s>]/i', $html)) {{\n"
    "        $site_name = get_bloginfo('name');\n"
    "        $h1_tag = '<h1 style=\"position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0\">' . esc_html($site_name) . '</h1>';\n"
    '        $html = preg_replace(\'/<body[^>]*>/i\', \'$0\' . \"\\n\" . $h1_tag, $html, 1);\n'
    '    }}\n'
    '    // 5d. Lazy loading en todas las im'
)

# Show first 50 chars of both
print('snippet[:350]:')
print(repr(snippet[:350]))
print()
print('old_h1:')
print(repr(old_h1))
print()

# Find where they differ
for i in range(min(len(snippet), len(old_h1))):
    if snippet[i] != old_h1[i]:
        print(f'Diff at pos {i}: snippet={repr(snippet[i:i+20])} old={repr(old_h1[i:i+20])}')
        break
else:
    if len(snippet) < len(old_h1):
        print(f'Snippet shorter by {len(old_h1)-len(snippet)} chars')
    elif len(old_h1) < len(snippet):
        print(f'Old shorter by {len(snippet)-len(old_h1)} chars')
    else:
        print('Exact match! (Why did .find say not found?)')
        print('Testing comparison...')
        if snippet[:len(old_h1)] == old_h1:
            print('Substring match confirmed')
        else:
            print('Substring mismatch despite char-by-char equality')
