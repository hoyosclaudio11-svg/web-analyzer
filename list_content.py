import os
import requests, base64, json

BASE = 'https://webanalyzer.com.ar/web/wp-json/wp/v2'
_wp_user = os.getenv("WP_USER", "a0110133")
_wp_pass = os.getenv("WP_APP_PASSWORD", "")
auth = base64.b64encode(f"{_wp_user}:{_wp_pass}".encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

print('=== PAGINAS ===')
r = requests.get(f'{BASE}/pages?per_page=50&status=publish,draft,pending', headers=headers)
pages = r.json()
for p in pages:
    print(f'  ID={p["id"]} slug={p["slug"]} status={p["status"]} title="{p["title"]["rendered"]}"')

print()
print('=== POSTS ===')
r = requests.get(f'{BASE}/posts?per_page=50&status=publish,draft,pending', headers=headers)
posts = r.json()
for p in posts:
    print(f'  ID={p["id"]} slug={p["slug"]} status={p["status"]} title="{p["title"]["rendered"]}"')

print()
print('=== SETTINGS (blog name, etc) ===')
r = requests.get(f'{BASE}/settings', headers=headers)
s = r.json()
print(f'  title={s.get("title")}')
print(f'  description={s.get("description")}')
print(f'  page_on_front={s.get("page_on_front")}')
print(f'  page_for_posts={s.get("page_for_posts")}')
print(f'  show_on_front={s.get("show_on_front")}')
