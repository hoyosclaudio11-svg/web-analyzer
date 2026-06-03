with open('E:/DelMonte/web-analyzer/analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('has_site_icon()')
if idx > 0:
    print(repr(content[idx-50:idx+250]))

print('---')

idx2 = content.find('5c. Si no hay H1')
if idx2 > 0:
    print(repr(content[idx2:idx2+350]))
