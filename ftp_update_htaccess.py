from ftplib import FTP_TLS
from io import BytesIO

ftp = FTP_TLS('a0110133.ferozo.com')
ftp.login('a0110133', 'U5Dc3gln@onM5uP')
ftp.prot_p()

# Leer actual
lines = []
ftp.retrlines('RETR /public_html/.htaccess', lines.append)
current = '\n'.join(lines)
print(f"Leido .htaccess actual: {len(current)} bytes")

# Guardar backup local
with open('E:/DelMonte/web-analyzer/htaccess_current.txt', 'w') as f:
    f.write(current)

# Backup remoto
ftp.storlines('STOR /public_html/.htaccess.backup_20260602', BytesIO(current.encode()))
print("Backup guardado en servidor")

# Insertar redirect despues de RewriteEngine On
redirect_rules = """# === Redirect raiz -> www (Render DNS 2026-06-02) ===
RewriteCond %{HTTP_HOST} ^webanalyzer\\.com\\.ar$ [NC]
RewriteRule ^(.*)$ https://www.webanalyzer.com.ar/$1 [R=301,L]

"""
new_content = current.replace("RewriteEngine On\n", "RewriteEngine On\n" + redirect_rules)

# Subir
ftp.storlines('STOR /public_html/.htaccess', BytesIO(new_content.encode()))
print("Nuevo .htaccess subido")

# Verificar
lines2 = []
ftp.retrlines('RETR /public_html/.htaccess', lines2.append)
print("\n=== Primeras 15 lineas ===")
for l in lines2[:15]:
    print(l)

ftp.quit()
print("\nOK")
