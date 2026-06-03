"""
AUTO-RUN: Espera a que la conexion se restaure y ejecuta la auditoria.
Ejecutar: python auto_run_audit.py
Se queda esperando hasta que riverplate-info.com.ar sea accesible.
"""
import requests
import time
import subprocess
import sys
import os

WORKDIR = os.path.dirname(os.path.abspath(__file__))
MASTER_SCRIPT = os.path.join(WORKDIR, "audit_master.py")
CHECK_INTERVAL = 30  # segundos entre cada chequeo
MAX_WAIT = 1800  # maximo 30 minutos de espera

print("=" * 60)
print("  AUTO-RUN: Esperando restauracion de conexion...")
print("  Chequeando cada 30 segundos (max 30 min)")
print("  Presiona Ctrl+C para cancelar")
print("=" * 60)
print()

start_time = time.time()

while True:
    elapsed = time.time() - start_time
    if elapsed > MAX_WAIT:
        print(f"\nTiempo maximo de espera agotado ({MAX_WAIT}s).")
        print("Ejecuta manualmente: python audit_master.py")
        sys.exit(1)
    
    try:
        r = requests.get("https://riverplate-info.com.ar", timeout=10)
        if r.status_code == 200:
            print(f"\nCONEXION RESTAURADA! (HTTP {r.status_code})")
            print(f"Espera total: {int(elapsed)} segundos")
            print()
            print("Ejecutando auditoria completa...")
            print()
            result = subprocess.run(
                [sys.executable, MASTER_SCRIPT],
                timeout=600,
            )
            sys.exit(result.returncode)
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.Timeout:
        pass
    except Exception as e:
        pass
    
    remaining = MAX_WAIT - int(elapsed)
    print(f"  [{int(elapsed)}s] Aun bloqueado... (restan {remaining}s)", end="\r")
    time.sleep(CHECK_INTERVAL)
