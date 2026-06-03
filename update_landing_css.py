"""
1. Lee el MU-plugin actual
2. Agrega CSS para secciones de venta (pricing, how-to, testimonials, FAQ, CTA)
3. Sube via FTP
"""
import os
import ftplib, ssl, io

HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(HOST, timeout=15, context=context)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()
ftp.cwd("/public_html/web/wp-content/mu-plugins")

# Leer archivo actual
current = []
ftp.retrlines("RETR wa-dark-theme.php", current.append)
current_content = "\n".join(current)

print(f"Archivo actual: {len(current_content)} caracteres, {len(current)} lineas")

# =====================================================================
# NUEVO CSS PARA SECCIONES DE VENTA
# =====================================================================

SALES_CSS = r"""
/* ===== HOW IT WORKS (3 pasos) ===== */
.wa-how-section {
  max-width: 800px;
  margin: 48px auto;
  padding: 0 20px;
  text-align: center;
}
.wa-how-section .wa-section-eyebrow {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #58a6ff;
  margin-bottom: 8px;
  font-weight: 600;
}
.wa-how-section .wa-section-title {
  font-size: 26px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8px;
}
.wa-how-section .wa-section-sub {
  font-size: 14px;
  color: #8b949e;
  margin-bottom: 36px;
}
.wa-steps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  text-align: center;
}
.wa-step-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 28px 20px 24px;
  position: relative;
  transition: border-color 0.2s, transform 0.2s;
}
.wa-step-card:hover {
  border-color: #58a6ff;
  transform: translateY(-2px);
}
.wa-step-num {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #1f6feb;
  color: #fff;
  font-size: 16px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
}
.wa-step-card h3 {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px;
}
.wa-step-card p {
  font-size: 12px;
  color: #8b949e;
  line-height: 1.5;
  margin: 0;
}

/* ===== PRICING TABLE ===== */
.wa-pricing-section {
  max-width: 750px;
  margin: 48px auto;
  padding: 0 20px;
  text-align: center;
}
.wa-pricing-section .wa-section-eyebrow {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #d29922;
  margin-bottom: 8px;
  font-weight: 600;
}
.wa-pricing-section .wa-section-title {
  font-size: 26px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8px;
}
.wa-pricing-section .wa-section-sub {
  font-size: 14px;
  color: #8b949e;
  margin-bottom: 36px;
}
.wa-pricing-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  text-align: left;
}
.wa-pricing-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 32px 24px;
  position: relative;
  transition: border-color 0.2s, transform 0.2s;
}
.wa-pricing-card:hover {
  transform: translateY(-2px);
}
.wa-pricing-card.pro {
  border-color: #d29922;
  background: linear-gradient(135deg, #1a1a0a 0%, #161b22 100%);
  box-shadow: 0 0 20px rgba(210, 153, 34, 0.08);
}
.wa-pricing-card.free:hover {
  border-color: #58a6ff;
}
.wa-pricing-badge {
  position: absolute;
  top: -12px;
  right: 20px;
  background: #d29922;
  color: #000;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.wa-pricing-card h3 {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 4px;
}
.wa-pricing-card .wa-price {
  font-size: 32px;
  font-weight: 800;
  color: #fff;
  margin: 8px 0 4px;
}
.wa-pricing-card .wa-price small {
  font-size: 14px;
  font-weight: 400;
  color: #8b949e;
}
.wa-pricing-card .wa-price-sub {
  font-size: 11px;
  color: #6e7681;
  margin-bottom: 20px;
}
.wa-pricing-card ul {
  list-style: none;
  padding: 0;
  margin: 0 0 24px;
}
.wa-pricing-card ul li {
  padding: 6px 0;
  font-size: 13px;
  color: #c9d1d9;
  border-bottom: 1px solid #21262d;
}
.wa-pricing-card ul li.check::before {
  content: "\2713 ";
  color: #3fb950;
  font-weight: bold;
}
.wa-pricing-card ul li.cross::before {
  content: "\2717 ";
  color: #f85149;
  font-weight: bold;
}
.wa-pricing-card .wa-btn {
  display: block;
  text-align: center;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  border: none;
  transition: background 0.15s, opacity 0.15s;
}
.wa-pricing-card .wa-btn:hover {
  opacity: 0.9;
}
.wa-btn-free {
  background: #21262d;
  color: #58a6ff;
  border: 1px solid #30363d;
}
.wa-btn-free:hover {
  background: #30363d;
  opacity: 1;
}
.wa-btn-pro {
  background: #d29922;
  color: #000;
}
.wa-btn-pro:hover {
  background: #e5a830;
  opacity: 1;
}
.wa-pricing-card .wa-garantia {
  font-size: 10px;
  color: #6e7681;
  text-align: center;
  margin-top: 12px;
}

/* ===== ANCLAJE DE PRECIO (consultoria) ===== */
.wa-anclaje {
  max-width: 650px;
  margin: 32px auto 0;
  background: rgba(88, 166, 255, 0.06);
  border: 1px solid rgba(88, 166, 255, 0.2);
  border-radius: 10px;
  padding: 20px 24px;
  text-align: center;
}
.wa-anclaje p {
  font-size: 13px;
  color: #8b949e;
  line-height: 1.6;
  margin: 0;
}
.wa-anclaje strong {
  color: #58a6ff;
}

/* ===== TESTIMONIALS / ESCENARIOS ===== */
.wa-testimonials-section {
  max-width: 800px;
  margin: 48px auto;
  padding: 0 20px;
  text-align: center;
}
.wa-testimonials-section .wa-section-eyebrow {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #3fb950;
  margin-bottom: 8px;
  font-weight: 600;
}
.wa-testimonials-section .wa-section-title {
  font-size: 26px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8px;
}
.wa-testimonials-section .wa-section-sub {
  font-size: 14px;
  color: #8b949e;
  margin-bottom: 36px;
}
.wa-testimonials-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  text-align: left;
}
.wa-testimonial-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  padding: 24px 20px;
  transition: border-color 0.2s;
}
.wa-testimonial-card:hover {
  border-color: #3fb950;
}
.wa-testimonial-card .wa-scenario-icon {
  font-size: 32px;
  margin-bottom: 10px;
}
.wa-testimonial-card h4 {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px;
}
.wa-testimonial-card p {
  font-size: 12px;
  color: #8b949e;
  line-height: 1.6;
  margin: 0 0 12px;
}
.wa-testimonial-card .wa-result {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: #3fb950;
  background: rgba(63, 185, 80, 0.1);
  padding: 4px 10px;
  border-radius: 12px;
}

/* ===== FAQ CONDENSADO ===== */
.wa-faq-section {
  max-width: 700px;
  margin: 48px auto;
  padding: 0 20px;
  text-align: center;
}
.wa-faq-section .wa-section-eyebrow {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #8b949e;
  margin-bottom: 8px;
  font-weight: 600;
}
.wa-faq-section .wa-section-title {
  font-size: 26px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8px;
}
.wa-faq-section .wa-section-sub {
  font-size: 14px;
  color: #8b949e;
  margin-bottom: 36px;
}
.wa-faq-item-condensed {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 18px 20px;
  margin-bottom: 10px;
  text-align: left;
}
.wa-faq-item-condensed.destacada {
  border-color: rgba(210, 153, 34, 0.4);
  background: rgba(210, 153, 34, 0.06);
}
.wa-faq-item-condensed h4 {
  font-size: 14px;
  font-weight: 600;
  color: #58a6ff;
  margin: 0 0 6px;
}
.wa-faq-item-condensed.destacada h4 {
  color: #d29922;
}
.wa-faq-item-condensed p {
  font-size: 12px;
  color: #8b949e;
  line-height: 1.5;
  margin: 0;
}
.wa-faq-link {
  display: inline-block;
  margin-top: 16px;
  font-size: 13px;
  color: #58a6ff;
  text-decoration: none;
  font-weight: 600;
}
.wa-faq-link:hover {
  text-decoration: underline;
}

/* ===== FINAL CTA DUAL ===== */
.wa-cta-section {
  max-width: 650px;
  margin: 48px auto 32px;
  padding: 40px 24px;
  text-align: center;
  background: linear-gradient(135deg, #161b22 0%, #1a1a2e 100%);
  border: 1px solid #30363d;
  border-radius: 16px;
}
.wa-cta-section h2 {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px;
}
.wa-cta-section .wa-cta-sub {
  font-size: 14px;
  color: #8b949e;
  margin-bottom: 28px;
  line-height: 1.5;
}
.wa-cta-buttons {
  display: flex;
  gap: 14px;
  justify-content: center;
  flex-wrap: wrap;
  align-items: center;
}
.wa-cta-btn {
  display: inline-block;
  padding: 14px 32px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  border: none;
  transition: background 0.15s, opacity 0.15s;
}
.wa-cta-btn:hover {
  opacity: 0.9;
}
.wa-cta-primary {
  background: #d29922;
  color: #000;
}
.wa-cta-primary:hover {
  background: #e5a830;
  opacity: 1;
}
.wa-cta-secondary {
  background: #21262d;
  color: #58a6ff;
  border: 1px solid #30363d;
}
.wa-cta-secondary:hover {
  background: #30363d;
  opacity: 1;
}
.wa-cta-urgency {
  font-size: 11px;
  color: #6e7681;
  margin-top: 16px;
}

/* ===== RESPONSIVE ===== */
@media (max-width: 768px) {
  .wa-steps-grid,
  .wa-testimonials-grid {
    grid-template-columns: 1fr;
  }
  .wa-pricing-grid {
    grid-template-columns: 1fr;
  }
  .wa-pricing-card.pro {
    order: -1;
  }
  .wa-cta-buttons {
    flex-direction: column;
  }
  .wa-cta-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .wa-section-title {
    font-size: 22px !important;
  }
  .wa-pricing-card {
    padding: 24px 16px;
  }
  .wa-pricing-card .wa-price {
    font-size: 26px;
  }
  .wa-testimonial-card {
    padding: 18px 14px;
  }
}
"""

# Insertar antes del cierre </style>
if "</style>" in current_content:
    new_content = current_content.replace("</style>", SALES_CSS + "\n</style>")
    bio = io.BytesIO(new_content.encode("utf-8"))
    ftp.storbinary("STOR wa-dark-theme.php", bio)
    print(f">>> CSS de ventas agregado ({len(SALES_CSS)} caracteres)")
else:
    print("ERROR: No se encontro </style> en el archivo")
    ftp.quit()
    exit(1)

ftp.quit()
print("CSS actualizado correctamente.")
