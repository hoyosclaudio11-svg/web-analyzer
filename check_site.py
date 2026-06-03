import requests, re

r = requests.get('https://webanalyzer.com.ar/web/')
html = r.text

# Buscar nuestro CSS
idx = html.find('WEB ANALYZER DARK THEME')
if idx > 0:
    print('MU-plugin CSS encontrado en posicion:', idx)
    print(html[idx:idx+600])
else:
    print('MU-plugin CSS NO encontrado')

# Buscar body background styles
print('\n=== Body styles ===')
bg_styles = re.findall(r'body\{[^}]*\}', html, re.IGNORECASE)
for s in bg_styles[:5]:
    print(' ', s[:200])

# Ver theme
twentys = html.count('twentytwentythree')
print(f'\n=== Tema: twentytwentythree referencias = {twentys} ===')

# Verifica si global-styles-inline-css esta
idx2 = html.find('global-styles-inline-css')
if idx2 > 0:
    print('\nGlobal styles inline:')
    print(html[idx2:idx2+1000])

# Ver fuentes cargadas
fonts = re.findall(r'font-family:[^;"]+', html)
print('\n=== Font families usadas ===')
for f in set(fonts):
    print(' ', f[:100])

print('\n=== Total HTML length:', len(html))
