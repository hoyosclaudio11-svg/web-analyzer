/**
 * Web Analyzer & Optimizer — Frontend
 */
const API = '/api/analyze';
const DOWNLOAD = '/api/download';
const HISTORY = '/api/history';

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ---------- State ----------
let currentReportHash = null;

function getUserToken() {
  return localStorage.getItem('wa_token') || '';
}

function apiHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  const token = getUserToken();
  if (token) headers['X-User-Token'] = token;
  return headers;
}

// =============================================================================
// Init
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
  const form = $('#analyze-form');
  const input = $('#url-input');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = input.value.trim();
    if (!url) return;
    await analyze(url);
  });

  loadHistory();
  loadStats();

  // Auto-analizar o mostrar bienvenida
  const params = new URLSearchParams(window.location.search);
  const analyzeUrl = params.get('analyze_url');
  const wasWelcome = params.get('welcome');
  if (wasWelcome === '1') {
    showNotification('🎉 ¡Bienvenido! Tu cuenta está lista. Analizá cualquier sitio gratis.');
    window.history.replaceState({}, '', '/');
  }
  if (analyzeUrl) {
    input.value = analyzeUrl;
    analyze(analyzeUrl).then(() => {
      window.history.replaceState({}, '', '/');
    });
  } else if (!wasWelcome) {
    input.focus();
  }
});

// =============================================================================
// API calls
// =============================================================================

async function analyze(url) {
  showLoading(true);
  hideResults();
  hideError();

  $('#status-text').textContent = 'Analizando...';
  $('#btn-analyze').disabled = true;

  try {
    const resp = await fetch(API, {
      method: 'POST',
      headers: apiHeaders(),
      body: JSON.stringify({ url }),
    });

    const data = await resp.json();

    if (!resp.ok) {
      showError(data.error || `Error HTTP ${resp.status}`);
      return;
    }

    if (data.errores && data.errores.length) {
      showError(data.errores[0]);
      return;
    }

    renderResults(data);
    $('#status-text').textContent = 'Completado';
  } catch (err) {
    showError(`Error de conexión: ${err.message}`);
  } finally {
    showLoading(false);
    $('#btn-analyze').disabled = false;
    loadHistory();
  }
}

async function loadHistory() {
  try {
    const resp = await fetch(HISTORY, { headers: apiHeaders() });
    const data = await resp.json();
    renderHistory(data);
  } catch (err) {
    // Silencioso — el historial no es crítico
  }
}

async function loadStats() {
  try {
    const resp = await fetch('/api/stats');
    const data = await resp.json();
    if (data.analyses && data.analyses > 0) {
      $('#stat-analyses').textContent = data.analyses.toLocaleString();
      $('#stat-pages').textContent = (data.pages || data.analyses).toLocaleString();
    }
  } catch (err) {
    // Silencioso
  }
}

// =============================================================================
// Auth
// =============================================================================

let authMode = 'login';

function openAuthModal() {
  authMode = 'login';
  updateAuthModalUI();
  $('#auth-modal').style.display = 'flex';
  $('#auth-email').focus();
}

function closeAuthModal() {
  $('#auth-modal').style.display = 'none';
}

function updateAuthModalUI() {
  $('#auth-modal-title').textContent = authMode === 'login' ? 'Creá tu cuenta gratis para descargar' : 'Creá tu cuenta gratis';
  $('#auth-submit-btn').textContent = authMode === 'login' ? 'Ingresar' : 'Crear cuenta';
  $('#auth-toggle').textContent = authMode === 'login' ? 'Registrate gratis' : 'Ya tengo cuenta';
  $('#auth-error').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
  // Auth modal events
  const modal = $('#auth-modal');
  if (modal) {
    $('#modal-close')?.addEventListener('click', closeAuthModal);
    modal.querySelector('.modal-overlay')?.addEventListener('click', closeAuthModal);
  }

  $('#auth-toggle')?.addEventListener('click', (e) => {
    e.preventDefault();
    authMode = authMode === 'login' ? 'register' : 'login';
    updateAuthModalUI();
  });

  $('#auth-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = $('#auth-email').value.trim();
    const password = $('#auth-password').value.trim();

    if (!email || !password) {
      showAuthError('Completá todos los campos.');
      return;
    }

    const endpoint = authMode === 'login' ? '/api/auth/login' : '/api/auth/register';
    try {
      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await resp.json();

      if (!resp.ok) {
        showAuthError(data.error || 'Error al procesar la solicitud.');
        return;
      }

      // Guardar sesion
      if (data.token) {
        localStorage.setItem('wa_token', data.token);
      }
      closeAuthModal();
      updateAuthUI();

      showNotification(authMode === 'login' ? '¡Bienvenido de nuevo!' : '¡Cuenta creada! Ya podés descargar.');

      // Continuar flujo pendiente: feedback o resultados completos
      var dataToResume = feedbackData || pendingData;
      if (dataToResume) {
        // Si ya está logueado, mostrar feedback o resultados
        if (getUserToken()) {
          checkFeedbackAndProceed(dataToResume);
        } else {
          renderFullResults(dataToResume);
        }
      }
    } catch (err) {
      showAuthError('Error de conexión. Probá de nuevo.');
    }
  });

  // Check session on load
  checkSession();
});

function showAuthError(msg) {
  const el = $('#auth-error');
  el.textContent = msg;
  el.style.display = 'block';
}

async function checkSession() {
  const token = localStorage.getItem('wa_token');
  if (!token) return;
  try {
    const resp = await fetch('/api/auth/me', {
      headers: { 'X-User-Token': token },
    });
    if (resp.ok) {
      const data = await resp.json();
      if (data.authenticated) {
        renderAuthUI(data);
      }
    }
  } catch (err) {
    // Silencioso
  }
}

function updateAuthUI() {
  const token = localStorage.getItem('wa_token');
  if (!token) {
    renderAuthUI(null);
    return;
  }
  checkSession();
}

function renderAuthUI(userData) {
  const container = $('#header-right');
  if (!container) return;

  if (userData && userData.authenticated) {
    const tier = userData.tier || 'free';
    const tierLabel = tier === 'paid' ? 'PRO' : 'Free';
    container.innerHTML = `
      <span id="user-info" style="display:flex">
        <span class="user-tier-badge ${tier}">${tierLabel}</span>
        <span>${esc(userData.email)}</span>
      </span>
      <button class="btn-auth-outline" id="btn-logout">Salir</button>
    `;
    $('#btn-logout')?.addEventListener('click', () => {
      localStorage.removeItem('wa_token');
      renderAuthUI(null);
      showNotification('Sesión cerrada.');
    });
  } else {
    container.innerHTML = `
      <button class="btn-auth-outline" id="btn-login">Ingresar</button>
      <button class="btn-auth" id="btn-register">Crear cuenta</button>
      <span id="status-text" class="status-text">Listo</span>
    `;
    $('#btn-login')?.addEventListener('click', () => {
      authMode = 'login';
      openAuthModal();
    });
    $('#btn-register')?.addEventListener('click', () => {
      authMode = 'register';
      openAuthModal();
    });
  }
}

// =============================================================================
// Render
// =============================================================================

// Email-gate: guardar datos pendientes
let pendingData = null;

function renderResults(data) {
  currentReportHash = data.report_hash || null;
  // Guardar y mostrar gate (score + 2 hallazgos críticos + modal)
  pendingData = data;
  showResults();
  renderScorecard(data.scorecard, data.promedio, data.promedio_color);
  renderShareLink(data.report_url, data.url_final || data.url, data.promedio);
  // Mostrar solo 2 hallazgos como anticipo
  if (data.hallazgos && data.hallazgos.length) {
    var preview = data.hallazgos.slice(0, 2);
    $('#hallazgos-body').innerHTML = '<h3 style="color:#ff6b6b;margin-bottom:12px">Problemas encontrados en tu web</h3>' +
      preview.map(function(h) {
        var problema = typeof h === 'object' ? (h.problema || h.titulo || JSON.stringify(h)) : h;
        var categoria = typeof h === 'object' ? (h.categoria || '') : '';
        var gravedad = typeof h === 'object' ? (h.gravedad || '') : '';
        var header = categoria ? '<div class="hal-cat">' + esc(categoria) + (gravedad ? ' — ' + esc(gravedad) : '') + '</div>' : '';
        return '<div class="hallazgo-item">' + header + '<strong>' + esc(problema) + '</strong></div>';
      }).join('');
  }
  // Ocultar el resto
  document.querySelectorAll('#recomendaciones-body, #soluciones-body, #next-steps-body, #next-steps-card, #meta-body, #imagenes-body, #scripts-body, #forms-body, .soluciones-card, .tech-bar, .details-grid').forEach(function(el) { if(el) el.style.display = 'none'; });
  // Mostrar modal de email
  showEmailGate();
}

function showEmailGate() {
  $('#email-gate-modal').style.display = 'flex';
}

function hideEmailGate() {
  $('#email-gate-modal').style.display = 'none';
}

function submitEmailGate(email) {
  if (!pendingData) return;
  hideEmailGate();
  // Enviar lead
  fetch('/api/lead', {
    method: 'POST',
    headers: apiHeaders(),
    body: JSON.stringify({
      email: email,
      url: pendingData.url || pendingData.url_final,
      promedio: pendingData.promedio,
      report_hash: pendingData.report_hash
    })
  }).catch(function(){});
  // Pasar a encuesta de feedback
  checkFeedbackAndProceed(pendingData);
}

function renderFullResults(data) {
  // Restaurar secciones ocultas
  document.querySelectorAll('#recomendaciones-body, #soluciones-body, #next-steps-body, #next-steps-card, #meta-body, #imagenes-body, #scripts-body, #forms-body, .soluciones-card, .tech-bar, .details-grid').forEach(function(el) { if(el) el.style.display = ''; });
  renderNextSteps(data);
  renderTech(data.tecnologia);
  renderHallazgos(data.hallazgos);
  renderRecomendaciones(data.recomendaciones);
  renderSoluciones(data.soluciones);
  renderMeta(data.meta);
  renderImagenes(data.imagenes);
  renderScripts(data.scripts);
  renderForms(data.forms);
  pendingData = null;
}

// =============================================================================
// Feedback modal
// =============================================================================

let feedbackRating = 0;
let feedbackData = null;

function showFeedbackModal(data, isLoggedIn) {
  feedbackData = data;
  feedbackRating = 0;
  document.querySelectorAll('#star-rating .star').forEach(function(s) { s.classList.remove('active'); });
  $('#feedback-comment').value = '';
  $('#feedback-updates').checked = false;
  var submitBtn = $('#feedback-submit-btn');
  if (!isLoggedIn) {
    submitBtn.textContent = 'Crear cuenta gratis y ver resultados';
    submitBtn.style.background = '#2563eb';
    submitBtn.style.color = '#fff';
  } else {
    submitBtn.textContent = 'Listo, ver mis resultados';
    submitBtn.style.background = '#3fb950';
    submitBtn.style.color = '#000';
  }
  $('#feedback-modal').style.display = 'flex';
}

function hideFeedbackModal() {
  $('#feedback-modal').style.display = 'none';
}

function checkFeedbackAndProceed(data) {
  feedbackData = data;
  var token = getUserToken();
  if (!token) {
    showFeedbackModal(data, false);
    return;
  }
  showFeedbackModal(data, true);
}

// Email gate form
document.addEventListener('DOMContentLoaded', function() {
  var form = document.getElementById('email-gate-form');
  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var email = document.getElementById('email-gate-input').value.trim();
      if (email) submitEmailGate(email);
    });
  }
  var skip = document.getElementById('email-gate-skip');
  if (skip) {
    skip.addEventListener('click', function(e) {
      e.preventDefault();
      hideEmailGate();
      if (pendingData) checkFeedbackAndProceed(pendingData);
    });
  }
  // Cerrar modal al hacer clic en el overlay
  var gateModal = document.getElementById('email-gate-modal');
  if (gateModal) {
    gateModal.querySelector('.modal-overlay')?.addEventListener('click', function() {
      hideEmailGate();
      if (pendingData) checkFeedbackAndProceed(pendingData);
    });
  }
});

function renderScorecard(scorecard, promedio, color) {
  const grid = $('#scorecard-grid');
  grid.innerHTML = '';

  const tooltips = {
    'Rendimiento': 'Velocidad de carga, scripts bloqueantes, lazy loading de imágenes y formatos optimizados.',
    'Accesibilidad': 'Alt text en imágenes, contraste de color, estructura de headings y formularios con labels.',
    'SEO': 'Meta tags (title, description, OG), canonical, headings semánticos y longitud de títulos.',
    'UX': 'Tiempo de carga, diseño responsive, legibilidad, contraste visual y jerarquía de contenido.',
    'Conversión': 'Formularios de captura de email, CTAs visibles, newsletter y oportunidades de conversión.',
  };

  for (const [cat, info] of Object.entries(scorecard)) {
    const puntaje = info.puntaje;
    const col = info.color;
    const detalles = (info.detalles || []).map(d => `<span>${esc(d)}</span>`).join('<br>');
    const tip = tooltips[cat] || '';

    grid.innerHTML += `
      <div class="score-card">
        <div class="cat-name" data-tooltip="${esc(tip)}">${esc(cat)}</div>
        <div class="cat-score ${col}">${puntaje}/10</div>
        ${detalles ? `<div class="cat-details">${detalles}</div>` : ''}
      </div>`;
  }

  $('#scorecard-promedio').innerHTML = `
    <span style="color:var(--text2)">PROMEDIO</span>
    <span class="prom-num ${color}">${promedio}/10</span>
    <span class="${color}" style="font-size:12px">${promedio >= 8 ? 'Listo para monetizar' : promedio >= 5 ? 'Necesita mejoras' : 'Requiere intervención'}</span>`;
}

function renderShareLink(reportUrl, url, promedio) {
  if (!reportUrl) return;
  const fullUrl = window.location.origin + reportUrl;
  let section = $('#share-section');
  if (!section) {
    section = document.createElement('section');
    section.id = 'share-section';
    section.className = 'share-section';
    const target = $('#scorecard-promedio');
    target.parentNode.insertBefore(section, target.nextSibling);
  }
  section.innerHTML = `
    <div class="share-box">
      <span class="share-url">${esc(fullUrl)}</span>
      <button class="btn-copy" data-url="${esc(fullUrl)}">Copiar</button>
    </div>`;
  section.querySelector('.btn-copy').addEventListener('click', function () {
    const url = this.getAttribute('data-url');
    navigator.clipboard.writeText(url).then(() => {
      this.textContent = 'Copiado!';
      this.classList.add('copied');
      setTimeout(() => { this.textContent = 'Copiar'; this.classList.remove('copied'); }, 2000);
    }).catch(() => {
      prompt('Copiá esta URL:', url);
    });
  });
}

function renderTech(tech) {
  const bar = $('#tech-bar');
  if (!tech || !tech.length) {
    bar.innerHTML = '<span style="font-size:11px;color:var(--text3)">Tecnología no detectada</span>';
    return;
  }
  bar.innerHTML = tech.map(t => `<span class="tech-tag">${esc(t)}</span>`).join('');
}

function renderHallazgos(hallazgos) {
  const body = $('#hallazgos-body');
  if (!hallazgos || !hallazgos.length) {
    body.innerHTML = '<p class="empty-text">Sin hallazgos críticos.</p>';
    return;
  }
  body.innerHTML = hallazgos.map(h => `
    <div class="hallazgo-item">
      <div class="hal-cat">${esc(h.categoria)} — ${esc(h.gravedad)}</div>
      <strong>${esc(h.problema)}</strong>
      ${h.impacto ? `<div style="font-size:11px;color:var(--text3);margin-top:4px">Impacto: ${esc(h.impacto)}</div>` : ''}
    </div>`).join('');
}

function renderRecomendaciones(recs) {
  const body = $('#recomendaciones-body');
  if (!recs || !recs.length) {
    body.innerHTML = '<p class="empty-text">Sin recomendaciones.</p>';
    return;
  }
  body.innerHTML = recs.map(r => `
    <div class="rec-item">
      <div class="rec-titulo">${esc(r.categoria)} — ${esc(r.titulo)}</div>
      <div style="margin-top:4px"><strong>Problema:</strong> ${esc(r.problema)}</div>
      <div style="margin-top:4px"><strong>Solución:</strong> ${esc(r.solucion)}</div>
      <div class="rec-meta">Esfuerzo: ${esc(r.esfuerzo)}</div>
    </div>`).join('');
}

function renderNextSteps(data) {
  const body = $('#next-steps-body');
  const scorecard = data.scorecard;
  const promedio = data.promedio;
  const tech = data.tecnologia || [];
  const soluciones = data.soluciones || [];
  const isWordPress = tech.some(t => t.toLowerCase().includes('wordpress'));

  let steps = [];
  let stepNum = 1;

  // Determinar qué archivo es la solución principal
  const pluginFile = soluciones.find(s => s.tipo === 'zip' || s.tipo === 'php');
  const mdFile = soluciones.find(s => s.tipo === 'markdown');
  const htmlFile = soluciones.find(s => s.tipo === 'html');

  // Paso 1: descargar según plataforma
  if (isWordPress && pluginFile) {
    steps.push({
      num: stepNum++,
      title: `Descargá el plugin WordPress (.zip)`,
      desc: `Hacé clic en <strong>"Descargar"</strong> en el archivo <strong>.zip</strong>. Es un plugin autocontenido listo para instalar que corrige automáticamente los problemas detectados.`,
      action: 'descargar',
      file: pluginFile,
      cta: `Descargar ${pluginFile.nombre}`,
    });
    steps.push({
      num: stepNum++,
      title: 'Instalalo en WordPress',
      desc: 'WordPress Admin → Plugins → Añadir nuevo → <strong>Subir plugin</strong> → Seleccioná el archivo .zip que descargaste → Instalar ahora → Activar.',
      action: 'hacer',
      cta: null,
    });
  } else if (htmlFile) {
    steps.push({
      num: stepNum++,
      title: `Descargá los archivos corregidos`,
      desc: `Hacé clic en <strong>"Descargar"</strong> en el archivo <strong>.html</strong>. Contiene fragmentos de HTML listos para copiar y pegar en tu sitio.`,
      action: 'descargar',
      file: htmlFile,
      cta: `Descargar ${htmlFile.nombre}`,
    });
    steps.push({
      num: stepNum++,
      title: 'Reemplazá el código en tu sitio',
      desc: 'Abrí el archivo descargado. Copiá cada fragmento en la sección correspondiente del HTML de tu sitio. Si usás un CMS, pegá el código en el editor de templates.',
      action: 'hacer',
      cta: null,
    });
  }

  // Paso: leer guía de corrección (solo si NO hay plugin WordPress)
  if (mdFile && !pluginFile) {
    steps.push({
      num: stepNum++,
      title: `Leé la guía de corrección`,
      desc: `El archivo <strong>.md</strong> explica paso a paso cada corrección necesaria. Abrirlo con cualquier editor de texto.`,
      action: 'descargar',
      file: mdFile,
      cta: `Descargar ${mdFile.nombre}`,
    });
  }

  // Paso: verificar resultados
  steps.push({
    num: stepNum++,
    title: 'Verificá los cambios en 48 horas',
    desc: 'Después de aplicar las correcciones, volvé a analizar la URL para confirmar que los puntajes mejoraron. El objetivo es llegar a <strong style="color:var(--green)">8/10</strong> en todas las categorías.',
    action: 'reanalizar',
    cta: null,
  });

  // Paso: programar recordatorio (guardar URL para re-análisis)
  steps.push({
    num: stepNum++,
    title: 'Programá un recordatorio',
    desc: 'Guardá esta URL en tus recordatorios y volvé en <strong>48-72 horas</strong> para re-analizar. Si instalaste el plugin, vas a ver la mejora reflejada en el scorecard.',
    action: 'recordatorio',
    cta: null,
    reminder: data.url_final || data.url,
  });

  // Si el puntaje es bajo, agregar urgencia
  const needsUrgency = Object.entries(scorecard).filter(([_, info]) => info.puntaje <= 4).length > 0;

  let urgencyHTML = '';
  if (needsUrgency) {
    urgencyHTML = `<div class="next-steps-urgency">
      ⚠️ Hay problemas críticos que impiden monetizar. Aplicá las soluciones lo antes posible.
    </div>`;
  } else if (promedio >= 8) {
    urgencyHTML = `<div class="next-steps-ok">
      ✅ El sitio está en buen estado. Las soluciones descargables son para optimizar detalles menores.
    </div>`;
  }

  body.innerHTML = `
    ${urgencyHTML}
    <div class="next-steps-list">
      ${steps.map(s => {
        let actionHtml = '';
        if (s.cta && s.file) {
          const dlUrl = '/api/download/' + encodeURIComponent(s.file.nombre);
          const params = [];
          if (currentReportHash) params.push('report_hash=' + encodeURIComponent(currentReportHash));
          const ut = getUserToken(); if (ut) params.push('user_token=' + encodeURIComponent(ut));
          actionHtml = `<a href="${dlUrl}?${params.join('&')}" class="btn-download step-btn" download>
              ${s.cta}
            </a>`;
        }
        return `
        <div class="next-step-item">
          <div class="step-num ${s.action === 'descargar' ? 'step-download' : s.action === 'reanalizar' ? 'step-recheck' : s.action === 'recordatorio' ? 'step-reminder' : 'step-do'}">${s.num}</div>
          <div class="step-content">
            <div class="step-title">${s.title}</div>
            <div class="step-desc">${s.desc}</div>
            ${actionHtml}
          </div>
        </div>`;
      }).join('')}
    </div>`;
}

function renderSoluciones(soluciones) {
  const body = $('#soluciones-body');
  if (!soluciones || !soluciones.length) {
    body.innerHTML = '<p class="empty-text">Sin soluciones generadas.</p>';
    return;
  }
  body.innerHTML = soluciones.map(s => {
    const dlParams = [];
    if (currentReportHash) dlParams.push('report_hash=' + encodeURIComponent(currentReportHash));
    const ut2 = getUserToken(); if (ut2) dlParams.push('user_token=' + encodeURIComponent(ut2));
    return `
      <div class="solucion-item">
        <div class="sol-type">.${esc(s.tipo)}</div>
        <div class="sol-name">${esc(s.nombre)}</div>
        <div class="sol-desc">${esc(s.descripcion)}</div>
        <a href="${DOWNLOAD}/${encodeURIComponent(s.nombre)}?${dlParams.join('&')}" class="btn-download" download>Descargar</a>
      </div>`;
  }).join('');
}

function renderMeta(meta) {
  if (!meta) return;
  const rows = [];
  for (const [k, v] of Object.entries(meta)) {
    if (v) {
      rows.push(`<tr><td>${esc(k)}</td><td>${esc(String(v).substring(0, 200))}</td></tr>`);
    }
  }
  if (rows.length) {
    $('#meta-body').innerHTML = `<table><thead><tr><th>Campo</th><th>Valor</th></tr></thead><tbody>${rows.join('')}</tbody></table>`;
  }
}

function renderImagenes(imgs) {
  if (!imgs) return;
  $('#imagenes-body').innerHTML = `
    <table>
      <thead><tr><th>Total</th><th>Sin alt</th><th>Sin lazy</th><th>Formatos</th></tr></thead>
      <tbody><tr>
        <td>${imgs.total}</td>
        <td class="${imgs.sin_alt > 0 ? 'rojo' : 'verde'}">${imgs.sin_alt}</td>
        <td class="${imgs.sin_lazy > 0 ? 'amarillo' : 'verde'}">${imgs.sin_lazy}</td>
        <td>${esc((imgs.formatos || []).join(', ') || '—')}</td>
      </tr></tbody>
    </table>`;
}

function renderScripts(scripts) {
  if (!scripts) return;
  $('#scripts-body').innerHTML = `
    <table>
      <thead><tr><th>Total</th><th>Externos</th><th>Bloqueantes</th><th>Async/Defer</th></tr></thead>
      <tbody><tr>
        <td>${scripts.total}</td>
        <td>${scripts.externos}</td>
        <td class="${scripts.bloqueantes > 3 ? 'rojo' : scripts.bloqueantes > 0 ? 'amarillo' : 'verde'}">${scripts.bloqueantes}</td>
        <td class="${scripts.con_async_defer > 0 ? 'verde' : 'amarillo'}">${scripts.con_async_defer}</td>
      </tr></tbody>
    </table>`;
}

function renderForms(forms) {
  if (!forms) return;
  let html = `<table><thead><tr><th>Total</th><th>Con email</th><th>Estado</th></tr></thead>`;
  html += `<tbody><tr>
    <td>${forms.total}</td>
    <td>${forms.con_email}</td>
    <td class="${forms.con_email > 0 ? 'verde' : forms.total > 0 ? 'amarillo' : 'rojo'}">
      ${forms.con_email > 0 ? 'Captura email' : forms.total > 0 ? 'Sin captura' : 'Sin formularios'}
    </td>
  </tr></tbody></table>`;
  $('#forms-body').innerHTML = html;
}

function renderHistory(items) {
  const body = $('#history-body');
  if (!items || !items.length) {
    body.innerHTML = '<p class="empty-text">Sin análisis previos.</p>';
    return;
  }

  // Agrupar por URL para detectar re-análisis
  const grouped = {};
  items.forEach(h => {
    if (!grouped[h.url]) grouped[h.url] = [];
    grouped[h.url].push(h);
  });

  body.innerHTML = items.map((h, i) => {
    const prev = getPreviousScore(items, h.url, i);
    let deltaHtml = '';
    if (prev !== null) {
      const diff = h.promedio - prev;
      if (diff > 0) {
        deltaHtml = `<span class="hist-delta up">+${diff.toFixed(1)}</span>`;
      } else if (diff < 0) {
        deltaHtml = `<span class="hist-delta down">${diff.toFixed(1)}</span>`;
      } else {
        deltaHtml = `<span class="hist-delta same">=</span>`;
      }
    }
    const count = grouped[h.url].length;
    const reanalisisBadge = count > 1 && grouped[h.url][0] === h
      ? `<span class="reanalisis-badge">${count}x</span>` : '';

    return `
      <div class="historial-item">
        <span class="hist-url">${esc(h.url)}${reanalisisBadge}${deltaHtml}</span>
        <span class="hist-fecha">${esc(h.fecha)}</span>
        <span class="hist-score ${h.promedio >= 8 ? 'verde' : h.promedio >= 5 ? 'amarillo' : 'rojo'}">${h.promedio}/10</span>
      </div>`;
  }).join('');
}

function getPreviousScore(items, url, currentIndex) {
  for (let i = currentIndex - 1; i >= 0; i--) {
    if (items[i].url === url) return items[i].promedio;
  }
  return null;
}

// =============================================================================
// Feedback modal events + download interception
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
  // Estrellas clickeables
  var stars = document.querySelectorAll('#star-rating .star');
  stars.forEach(function(star) {
    star.addEventListener('click', function() {
      feedbackRating = parseInt(this.getAttribute('data-rating'));
      stars.forEach(function(s) {
        s.classList.toggle('active', parseInt(s.getAttribute('data-rating')) <= feedbackRating);
      });
    });
  });

  // Submit del feedback
  var submitBtn = $('#feedback-submit-btn');
  if (submitBtn) {
    submitBtn.addEventListener('click', async function() {
      var token = getUserToken();
      if (!token) {
        hideFeedbackModal();
        // Abrir auth y después de registrarse volver al feedback
        openAuthModalForFeedback(feedbackData);
        return;
      }
      if (feedbackRating > 0) {
        try {
          await fetch('/api/feedback', {
            method: 'POST',
            headers: apiHeaders(),
            body: JSON.stringify({
              report_hash: feedbackData.report_hash,
              rating: feedbackRating,
              comentario: $('#feedback-comment').value.trim(),
              recibir_updates: $('#feedback-updates').checked,
            }),
          });
        } catch (e) {}
      }
      hideFeedbackModal();
      if (feedbackData) renderFullResults(feedbackData);
    });
  }

  // Skip del feedback
  var skipFb = $('#feedback-skip');
  if (skipFb) {
    skipFb.addEventListener('click', function(e) {
      e.preventDefault();
      hideFeedbackModal();
      if (feedbackData) renderFullResults(feedbackData);
    });
  }

  // Cerrar feedback al hacer clic en overlay
  var fbModal = $('#feedback-modal');
  if (fbModal) {
    fbModal.querySelector('.modal-overlay')?.addEventListener('click', function() {
      hideFeedbackModal();
      if (feedbackData) renderFullResults(feedbackData);
    });
  }
});

// Abre auth y guarda intencion de volver al feedback
function openAuthModalForFeedback(data) {
  feedbackData = data;
  openAuthModal();
}

// Interceptar clicks en descargas premium para manejar auth/feedback
document.addEventListener('click', async function(e) {
  var link = e.target.closest('a[href*="/api/download/"]');
  if (!link) return;
  var href = link.getAttribute('href');
  if (!href) return;
  // Solo interceptar archivos premium
  var isPremium = href.indexOf('.zip') > -1 || href.indexOf('.json') > -1;
  if (!isPremium) return;

  e.preventDefault();
  try {
    var resp = await fetch(href);
    if (resp.status === 403) {
      var data = await resp.json();
      if (data.action === 'feedback_required') {
        showFeedbackModal(feedbackData || pendingData || { report_hash: currentReportHash }, true);
      } else {
        showNotification(data.error || 'Acceso denegado.');
      }
      return;
    }
    if (resp.status === 401) {
      openAuthModalForFeedback(feedbackData || pendingData || { report_hash: currentReportHash });
      return;
    }
    if (resp.ok) {
      var blob = await resp.blob();
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = href.split('/').pop().split('?')[0];
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } else {
      var errData = await resp.json().catch(function() { return {}; });
      showNotification(errData.error || 'Error al descargar.');
    }
  } catch (err) {
    showNotification('Error de conexion al descargar.');
  }
});

// =============================================================================
// UI helpers
// =============================================================================

function showLoading(show) {
  $('#loading').style.display = show ? 'flex' : 'none';
}

function showResults() {
  $('#results').style.display = 'block';
}

function hideResults() {
  $('#results').style.display = 'none';
}

function showError(msg) {
  const el = $('#error-box');
  el.innerHTML = `<strong>Error:</strong> ${esc(msg)}`;
  el.style.display = 'block';
  $('#status-text').textContent = 'Error';
}

function hideError() {
  $('#error-box').style.display = 'none';
}

function showNotification(msg) {
  const el = document.createElement('div');
  el.className = 'notification-toast';
  el.textContent = msg;
  document.body.appendChild(el);
  requestAnimationFrame(() => {
    el.classList.add('show');
    setTimeout(() => {
      el.classList.remove('show');
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });
}

function esc(str) {
  if (!str) return '';
  str = String(str);
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
