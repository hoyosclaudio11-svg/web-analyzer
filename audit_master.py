"""
AUDITORIA MAESTRA — River Plate Info
Ejecuta los 6 pasos del plan de implementacion en orden.
"""
import subprocess, sys, time, os

SCRIPTS = [
    ("Fase 1 - Paso 1: SEO Homepage", "audit_paso1_seo_home.py"),
    ("Fase 1 - Paso 2: OG Duplicados", "audit_paso2_og_duplicates.py"),
    ("Fase 2 - Pasos 3-4: Seguridad .htaccess", "audit_paso3_4_htaccess.py"),
    ("Fase 3 - Paso 5: Newsletter Duplicado", "audit_paso5_newsletter.py"),
    ("Fase 3 - Paso 6: Contraste CSS", "audit_paso6_contrast.py"),
]

WORKDIR = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("  AUDITORIA COMPLETA — riverplate-info.com.ar")
print("  Ejecutando 5 scripts de implementacion...")
print("=" * 60)
print()

# Verificar conectividad primero
import requests
print("Verificando conexion con riverplate-info.com.ar...")
try:
    r = requests.get("https://riverplate-info.com.ar", timeout=15)
    print(f"OK: HTTP {r.status_code} ({len(r.text)} chars)")
    print()
except Exception as e:
    print(f"ERROR: No se puede conectar - {e}")
    print("La IP puede estar bloqueada temporalmente por el firewall de Ferozo.")
    print("Espera 5-15 minutos y vuelve a intentar.")
    sys.exit(1)

results = []
for i, (name, script) in enumerate(SCRIPTS, 1):
    print(f"\n{'='*60}")
    print(f"  [{i}/{len(SCRIPTS)}] {name}")
    print(f"{'='*60}\n")
    
    script_path = os.path.join(WORKDIR, script)
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,
            timeout=120,
        )
        status = "OK" if result.returncode == 0 else f"ERROR (code {result.returncode})"
        results.append((name, status))
    except subprocess.TimeoutExpired:
        results.append((name, "TIMEOUT"))
        print(f"   TIMEOUT: {script} excedio 120 segundos")
    except Exception as e:
        results.append((name, f"EXCEPCION: {e}"))
    
    # Pausa entre scripts para evitar rate limiting
    if i < len(SCRIPTS):
        print("\nEsperando 3 segundos antes del siguiente paso...")
        time.sleep(3)

# Resumen final
print("\n\n" + "=" * 60)
print("  RESUMEN DE IMPLEMENTACION")
print("=" * 60)
for name, status in results:
    icon = "OK" if "OK" in status else "!!"
    print(f"  [{icon}] {name}: {status}")

ok_count = sum(1 for _, s in results if "OK" in s)
print(f"\n  {ok_count}/{len(results)} pasos completados exitosamente")
print("=" * 60)
