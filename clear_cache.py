"""Limpiar cache de WP Super Cache via FTP."""
import os
import ftplib, ssl

HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, context=ctx)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()

# Buscar directorio de cache
cache_dirs = ['/public_html/web/wp-content/cache/supercache', '/public_html/web/wp-content/cache']

for cache_dir in cache_dirs:
    try:
        ftp.cwd(cache_dir)
        print(f"Cache dir: {cache_dir}")

        # Limpiar archivos de cache
        count = 0
        for item in ftp.nlst():
            if item in ('.', '..'):
                continue
            try:
                # Intentar borrar archivos
                ftp.delete(item)
                count += 1
            except:
                # Puede ser directorio, intentar borrar recursivamente
                try:
                    ftp.cwd(item)
                    for sub in ftp.nlst():
                        if sub not in ('.', '..'):
                            try:
                                ftp.delete(sub)
                            except:
                                pass
                    ftp.cwd('..')
                    ftp.rmd(item)
                    count += 1
                except:
                    pass
        print(f"  {count} elementos eliminados")
    except Exception as e:
        print(f"  {cache_dir}: {e}")

ftp.quit()
print("\nCache limpiado.")
