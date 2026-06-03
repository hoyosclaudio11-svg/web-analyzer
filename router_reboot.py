"""Try to login to Huawei HG8145X6-10 router and reboot it."""
import requests
import base64
import re

session = requests.Session()

# Step 1: Get the main page
print("Step 1: Getting main page...")
r = session.get("http://192.168.1.1/", timeout=10)
print(f"Status: {r.status_code}")

# Step 2: Try login without token
print("\nStep 2: Trying login...")
credentials = [
    ("telecomadmin", "telecomadmin"),
    ("admin", "admin"),
    ("user", "user"),
    ("admin", "1234"),
    ("telecomadmin", "1234"),
]

for username, password in credentials:
    encoded_pass = base64.b64encode(password.encode()).decode()
    data = {
        "UserName": username,
        "PassWord": encoded_pass,
        "x.X_HW_Token": "",
    }
    try:
        r = session.post(
            "http://192.168.1.1/login.cgi",
            data=data,
            timeout=10,
            allow_redirects=False,
        )
        print(f"  {username}/{password}: HTTP {r.status_code}")
        cookies = dict(session.cookies)
        if cookies:
            print(f"    Cookies: {cookies}")
        if r.status_code == 302:
            print(f"    REDIRECT: {r.headers.get('Location', '')}")
        # Check if response contains reboot page or success indicators
        if "reboot" in r.text.lower() or "main" in r.text.lower():
            print(f"    POSSIBLE SUCCESS!")
            print(f"    Response preview: {r.text[:300]}")
    except Exception as e:
        print(f"  {username}/{password}: {e}")
