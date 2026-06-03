from ftplib import FTP_TLS

ftp = FTP_TLS('a0110133.ferozo.com')
ftp.login('a0110133', 'U5Dc3gln@onM5uP')
ftp.prot_p()

print("=== Directorio raiz ===")
ftp.retrlines('LIST /')

print("\n=== .htaccess actual ===")
try:
    lines = []
    ftp.retrlines('RETR /.htaccess', lines.append)
    print('\n'.join(lines))
    # Guardar en archivo
    with open('E:/DelMonte/web-analyzer/htaccess_original.txt', 'w') as f:
        f.write('\n'.join(lines))
    print("\nGuardado en htaccess_original.txt")
except Exception as e:
    print(f"Error: {e}")

ftp.quit()
