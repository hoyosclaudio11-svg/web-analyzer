import os
import ftplib, ssl, io

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()
ftp.cwd("/public_html/wp-content/mu-plugins")

data = io.BytesIO()
ftp.retrbinary("RETR wa-river-club.php", data.write)
ftp.quit()

content = data.getvalue().decode("utf-8", errors="replace")
print(f"File size: {len(content)} bytes")
print("Contains 'river_enqueue_bootstrap':", "river_enqueue_bootstrap" in content)
print("Contains 'wa-bootstrap':", "wa-bootstrap" in content)
print("Contains 'bootstrap' in Capa1 block:", 'bootstrap' in content.split('$block = [')[1].split('];')[0] if '$block = [' in content else "N/A")
print("Contains 'bootstrap' in Capa2 prefix:", 'bootstrap' in content.split('$block_prefix = [')[1].split('];')[0] if '$block_prefix = [' in content else "N/A")
print()
print("=== LAST 500 CHARS ===")
print(content[-500:])
