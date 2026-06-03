import os
import requests, base64, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
WP_USER = 'a0110133'; WP_PASS = os.getenv('WP_APP_PASSWORD', '')
BASE = 'https://webanalyzer.com.ar/web/wp-json/wp/v2'
auth = base64.b64encode(f'{WP_USER}:{WP_PASS}'.encode()).decode()
headers = {'Authorization': f'Basic {auth}'}

r = requests.get(f'{BASE}/pages/10', headers=headers, params={'context': 'edit'})
data = r.json()
raw = data.get('content', {}).get('raw', '')
# Remove the wp:html wrapper and show whats between
inner = raw.replace('<!-- wp:html -->', '').replace('<!-- /wp:html -->', '').strip()

# Find key section markers
markers = ['wa-hero', 'wa-carousel-wrapper', 'wa-ba-card', 'wa-features', 'Analizar gratis', 'Blog', 'footer']
for m in markers:
    idx = inner.find(m)
    if idx >= 0:
        print(f'  [{m}] at position {idx}')
    else:
        print(f'  [{m}] NOT FOUND')

# Show the middle portion around features area
print('\n=== MIDDLE (features area, ~ char 4000) ===')
print(inner[3800:5000])
print('\n=== END (after features, ~ char 6500) ===')
print(inner[6000:])
