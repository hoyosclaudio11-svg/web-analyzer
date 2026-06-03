import os
import ftplib, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ftp = ftplib.FTP_TLS(os.getenv('FTP_HOST_RIVER', 'a0070978.ferozo.com'), timeout=15, context=ctx)
ftp.login('a0070978', os.getenv('FTP_PASS_RIVER', ''))
ftp.prot_p()
ftp.cwd('/public_html/wp-content/mu-plugins')
lines = []
ftp.retrlines('RETR wa-river-theme.php', lambda l: lines.append(l))
code = '\n'.join(lines)
with open('E:/DelMonte/web-analyzer/current_wa_river_theme.php', 'w', encoding='utf-8') as f:
    f.write(code)
print(f"Leido: {len(code)} chars, {len(lines)} lineas")
ftp.quit()
