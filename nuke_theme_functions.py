"""Buscar y comentar los wp_enqueue_style en functions.php del tema."""
import os
import ftplib, ssl

HOST = os.getenv("FTP_HOST_RIVER", "a0070978.ferozo.com")
USER = "a0070978"
PASS = os.getenv("FTP_PASS_RIVER", "")
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=30, context=CONTEXT)
ftp.login(USER, PASS)
ftp.prot_p()

# Revisar functions.php del tema hijo (newstack)
print("=== FUNCTIONS.PHP (newstack) ===")
ftp.cwd("/public_html/wp-content/themes/newstack")
lines = []
ftp.retrlines("RETR functions.php", lambda l: lines.append(l))
code = "\n".join(lines)
print(f"Tamano: {len(code)} chars, {len(lines)} lineas")

# Guardar backup
with open("E:/DelMonte/web-analyzer/backup_functions_newstack.php", "w", encoding="utf-8") as f:
    f.write(code)
print("Backup local guardado")

# Buscar lineas de wp_enqueue_style
print("\n=== LINEAS CON wp_enqueue_style/script ===")
for i, line in enumerate(lines):
    if "wp_enqueue_style" in line or "wp_enqueue_script" in line:
        print(f"  L{i+1}: {line.strip()[:120]}")

# Tambien revisar functions.php del tema padre (newsup)
print("\n=== FUNCTIONS.PHP (newsup) ===")
ftp.cwd("/public_html/wp-content/themes/newsup")
lines2 = []
ftp.retrlines("RETR functions.php", lambda l: lines2.append(l))
code2 = "\n".join(lines2)
print(f"Tamano: {len(code2)} chars, {len(lines2)} lineas")

# Guardar backup
with open("E:/DelMonte/web-analyzer/backup_functions_newsup.php", "w", encoding="utf-8") as f:
    f.write(code2)
print("Backup local guardado")

print("\n=== LINEAS CON wp_enqueue_style/script ===")
for i, line in enumerate(lines2):
    if "wp_enqueue_style" in line or "wp_enqueue_script" in line:
        print(f"  L{i+1}: {line.strip()[:120]}")

ftp.quit()
