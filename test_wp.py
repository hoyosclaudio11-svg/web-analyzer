import requests, base64

user = 'a0110133'
pwd = 'era6 uQQE 0k9i hghY E0iM 2Akn'
auth = base64.b64encode(f'{user}:{pwd}'.encode()).decode()

# Probar users/me
r = requests.get('https://webanalyzer.com.ar/web/wp-json/wp/v2/users/me',
                 headers={'Authorization': f'Basic {auth}'})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

# Si falla, probar crear un post
if r.status_code != 200:
    print("\nProbando crear un post...")
    data = {
        'title': 'Test',
        'content': 'Test content',
        'status': 'draft'
    }
    r2 = requests.post('https://webanalyzer.com.ar/web/wp-json/wp/v2/posts',
                       headers={'Authorization': f'Basic {auth}'},
                       json=data)
    print(f"Status: {r2.status_code}")
    print(f"Response: {r2.text[:500]}")
