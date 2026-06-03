import requests
try:
    r = requests.get("https://riverplate-info.com.ar", timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Content length: {len(r.text)}")
    # Check for key elements
    for term in ["wa-river-club-theme", "EL MAS GRANDE", "river-hero", "menu-item"]:
        count = r.text.count(term)
        print(f"  '{term}': {count}")
    print("\n--- Primeros 500 chars ---")
    print(r.text[:500])
except Exception as e:
    print(f"Error: {e}")
