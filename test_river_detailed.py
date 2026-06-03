import requests
r = requests.get("https://riverplate-info.com.ar", timeout=30)
# Buscar el error real en el HTML
import re
# WordPress error pages have the error in a <p> or script tag
errors = re.findall(r'<p[^>]*>(.*?(?:error|Error|fatal|Fatal|PHP|php).*?)</p>', r.text, re.DOTALL)
for e in errors:
    print("ERROR:", e[:500])
# Also search for script with error
scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
for s in scripts:
    if 'error' in s.lower() or 'fatal' in s.lower():
        print("SCRIPT:", s[:500])
# Print more of the page
print("\n=== FULL BODY ===")
body_match = re.search(r'<body>(.*?)</body>', r.text, re.DOTALL)
if body_match:
    print(body_match.group(1)[:2000])
