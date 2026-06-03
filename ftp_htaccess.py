from ftplib import FTP_TLS

ftp = FTP_TLS('a0110133.ferozo.com')
ftp.login('a0110133', 'U5Dc3gln@onM5uP')
ftp.prot_p()

print("=== public_html ===")
ftp.retrlines('LIST /public_html')

print("\n=== .htaccess en public_html ===")
try:
    lines = []
    ftp.retrlines('RETR /public_html/.htaccess', lines.append)
    current = '\n'.join(lines)
    print(current)
    with open('E:/DelMonte/web-analyzer/htaccess_current.txt', 'w') as f:
        f.write(current)
except Exception as e:
    print(f"Error leyendo: {e}")
    current = ""

ftp.quit()
