import os
import ftplib, ssl, io, requests

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

# Paso 1: Subir CSS actualizado
print("1. Subiendo wa-river-club.php (CSS + disclaimer bar + anti-spam)...")
ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

with open("E:/DelMonte/web-analyzer/wa-river-theme-css.php", "rb") as f:
    data = f.read()
ftp.cwd("/public_html/wp-content/mu-plugins")
ftp.storbinary("STOR wa-river-club.php", io.BytesIO(data))
ftp.quit()
print("   CSS actualizado. Size: {} bytes".format(len(data)))

# Paso 2: Subir y ejecutar fix_legal.php
print("\n2. Subiendo fix_legal.php...")
ftp2 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp2.login(USER, PASS)
ftp2.prot_p()

with open("E:/DelMonte/web-analyzer/fix_legal.php", "rb") as f:
    data2 = f.read()
ftp2.cwd("/public_html")
ftp2.storbinary("STOR fix_legal.php", io.BytesIO(data2))
ftp2.quit()

# Paso 3: Ejecutar el script
print("\n3. Ejecutando fix_legal.php...")
r = requests.get("https://riverplate-info.com.ar/fix_legal.php", timeout=120)
print(r.text[:5000] if len(r.text) > 5000 else r.text)

# Paso 4: Limpiar
print("\n4. Eliminando fix_legal.php del servidor...")
ftp3 = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp3.login(USER, PASS)
ftp3.prot_p()
ftp3.cwd("/public_html")
ftp3.delete("fix_legal.php")
ftp3.quit()

# Paso 5: Verificar que el disclaimer aparece en el sitio
print("\n5. Verificando disclaimer en homepage...")
r2 = requests.get("https://riverplate-info.com.ar/", timeout=60)
has_disclaimer = "SITIO NO OFICIAL" in r2.text
has_bar = "river-disclaimer" in r2.text
has_css = "wa-river-club-theme" in r2.text
print(f"   Disclaimer en pagina: {has_disclaimer}")
print(f"   Barra disclaimer (#river-disclaimer): {has_bar}")
print(f"   Nuestro CSS cargado: {has_css}")

# Verificar Tienda
r3 = requests.get("https://riverplate-info.com.ar/tienda", timeout=60)
has_afiliado = "Enlace de afiliado" in r3.text or "NO es la tienda oficial" in r3.text
print(f"   Tienda con aviso afiliado: {has_afiliado}")

# Verificar Aviso Legal
r4 = requests.get("https://riverplate-info.com.ar/aviso-legal", timeout=60)
aviso_ok = "NO esta afiliado" in r4.text or "INDEPENDIENTE" in r4.text
print(f"   Pagina Aviso Legal OK: {aviso_ok}")

print("\n=== DEPLOY COMPLETADO ===")
