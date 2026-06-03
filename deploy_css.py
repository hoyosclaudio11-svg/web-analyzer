import os
import ftplib, ssl, io, requests

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

with open("E:/DelMonte/web-analyzer/wa-river-theme-css.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html/wp-content/mu-plugins")
ftp.storbinary("STOR wa-river-club.php", io.BytesIO(data))
ftp.quit()
print("CSS uploaded to mu-plugins/wa-river-club.php")

r = requests.get("https://riverplate-info.com.ar/", timeout=60)
css_count = r.text.count("wa-river-club-theme")
theme_css_count = r.text.count("newsup-style") + r.text.count("newstack-style") + r.text.count("bootstrap.css")
print(f"Pages: r.status_code, our CSS blocks: {css_count}, theme CSS: {theme_css_count}")
print("Done")
