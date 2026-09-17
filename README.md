# 🔎 Web Analyzer & Optimizer

> **EN:** Web auditor that analyzes public URLs — SEO, Open Graph, accessibility/contrast, multi-page crawls — monitors scores over time and generates downloadable fixes. Live at [webanalyzer.com.ar](https://webanalyzer.com.ar).

Analiza URLs públicas y genera soluciones descargables. Incluye cuentas de usuario, monitoreo de sitios y reportes compartibles. En producción con dominio propio.

## Funcionalidades

- **Análisis individual y multi-página** de URLs públicas (crawler interno)
- **Auditoría técnica**: SEO (títulos, metas, Open Graph), accesibilidad (contraste) y estructura del sitio
- **Cuentas de usuario** con autenticación por token, estadísticas de uso e historial de análisis
- **URLs monitoreadas** con evolución del score en el tiempo
- **Reportes compartibles** por enlace público
- **Rate limiting** por IP y planes de pago integrados con **Mercado Pago**

## Stack

Python · Flask · BeautifulSoup · PostgreSQL · Flask-Limiter · Gunicorn / Waitress

## Correr en local

```bash
pip install -r requirements.txt
python app.py
```

## Deploy

`Procfile` incluido (gunicorn) — compatible con Render, Railway o Heroku. La base de datos se configura con `DATABASE_URL` (PostgreSQL).

## Licencia

[MIT](LICENSE)
