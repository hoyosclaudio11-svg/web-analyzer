import os
import requests, ftplib, ssl, io
import urllib3
urllib3.disable_warnings()

FTP_HOST=os.getenv('FTP_HOST_WEBANALYZER', 'a0110133.ferozo.com'); FTP_USER='a0110133'; FTP_PASS=os.getenv('FTP_PASS_WEBANALYZER', '')
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

# Subir bridge debug
ftp = ftplib.FTP_TLS(FTP_HOST, timeout=15, context=ctx)
ftp.login(FTP_USER, FTP_PASS); ftp.prot_p()
ftp.cwd('/public_html/web')
with open('wa_bridge.php','rb') as f: bio=io.BytesIO(f.read())
ftp.storbinary('STOR wa_bridge.php', bio)
ftp.quit()
print('Bridge subido')

# Probar HTTP
print('---HTTP---')
try:
    r = requests.post('https://webanalyzer.com.ar/web/wa_bridge.php', data={'token':'test123','content':'hello'}, timeout=15)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:500]}')
    print(f'Redirect history: {[h.status_code for h in r.history]}')
except Exception as e:
    print(f'Error: {e}')

# Probar HTTPS
print('---HTTPS---')
try:
    r2 = requests.post('https://webanalyzer.com.ar/web/wa_bridge.php', data={'token':'test123','content':'hello'}, verify=False, timeout=15)
    print(f'Status: {r2.status_code}')
    print(f'Response: {r2.text[:500]}')
    print(f'Redirect history: {[h.status_code for h in r2.history]}')
except Exception as e:
    print(f'Error: {e}')

# Eliminar bridge
ftp = ftplib.FTP_TLS(FTP_HOST, timeout=15, context=ctx)
ftp.login(FTP_USER, FTP_PASS); ftp.prot_p()
ftp.cwd('/public_html/web')
ftp.delete('wa_bridge.php')
ftp.quit()
print('Bridge eliminado')
