import os
import ftplib, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ftp = ftplib.FTP_TLS(os.getenv('FTP_HOST_RIVER', 'a0070978.ferozo.com'), timeout=15, context=ctx)
ftp.login('a0070978', os.getenv('FTP_PASS_RIVER', ''))
ftp.prot_p()
ftp.cwd('/public_html/wp-content/mu-plugins')
files = []
ftp.retrlines('LIST', lambda l: files.append(l))
for f in files:
    print(f)
print("---")
# Ver si hay wa-river tematico
try:
    ftp.cwd('/public_html/wp-content/plugins/sportspress')
    print("SportsPress: INSTALADO")
except:
    print("SportsPress: NO instalado")
ftp.quit()
