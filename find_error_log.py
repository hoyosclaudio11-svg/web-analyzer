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

# Current directory after login
print("CWD:", ftp.pwd())

# List root
files = []
ftp.retrlines("LIST", lambda l: files.append(l))
for f in files:
    print(f)

# Check for public_html/error_log
print("\n=== Buscando error_log ===")
for path in ["error_log", "public_html/error_log", "public_html/wp-content/debug.log"]:
    try:
        ftp.cwd("/")
        lines = []
        ftp.retrlines(f"RETR {path}", lambda l: lines.append(l))
        print(f"\n{path}:")
        for line in lines[-30:]:
            print(line)
    except Exception as e:
        print(f"  {path}: {e}")

ftp.quit()
