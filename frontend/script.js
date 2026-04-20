// Orbital.AI — static JS (vanilla, no dependencies)

// Starfield canvas
(function () {
  const c = document.getElementById('starfield');
  if (!c) return;
  const ctx = c.getContext('2d');
  let stars = [], raf;
  function resize() {
    c.width = window.innerWidth; c.height = window.innerHeight;
    stars = [];
    const count = Math.min(180, Math.floor((c.width * c.height) / 12000));
    for (let i = 0; i < count; i++) {
      stars.push({
        x: Math.random() * c.width,
        y: Math.random() * c.height,
        z: Math.random() * 0.8 + 0.2,
        r: Math.random() * 1.4 + 0.2,
      });
    }
  }
  let t = 0;
  function draw() {
    ctx.clearRect(0, 0, c.width, c.height);
    t += 0.005;
    for (const s of stars) {
      const tw = 0.5 + 0.5 * Math.sin(t * 2 + s.x);
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r * s.z, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(186, 100%, ${70 + s.z * 20}%, ${0.3 + tw * 0.6 * s.z})`;
      ctx.fill();
      s.y += s.z * 0.05;
      if (s.y > c.height) s.y = 0;
    }
    raf = requestAnimationFrame(draw);
  }
  resize(); draw();
  window.addEventListener('resize', resize);
})();

// Scroll progress
(function () {
  const bar = document.getElementById('scrollProgress');
  function update() {
    const h = document.documentElement;
    const max = h.scrollHeight - h.clientHeight;
    const pct = max > 0 ? (h.scrollTop / max) * 100 : 0;
    bar.style.width = pct + '%';
  }
  document.addEventListener('scroll', update, { passive: true });
  update();
})();

// Compare slider
(function () {
  const root = document.getElementById('compare');
  if (!root) return;
  const before = document.getElementById('compareBefore');
  const handle = document.getElementById('compareHandle');
  const range = document.getElementById('compareSlider');
  function set(pct) {
    pct = Math.max(0, Math.min(100, pct));
    before.style.width = pct + '%';
    handle.style.left = pct + '%';
    range.value = pct;
  }
  range.addEventListener('input', (e) => set(parseFloat(e.target.value)));
  // pointer drag
  let dragging = false;
  function onMove(clientX) {
    const r = root.getBoundingClientRect();
    set(((clientX - r.left) / r.width) * 100);
  }
  root.addEventListener('pointerdown', (e) => { dragging = true; root.setPointerCapture(e.pointerId); onMove(e.clientX); });
  root.addEventListener('pointermove', (e) => { if (dragging) onMove(e.clientX); });
  root.addEventListener('pointerup',   (e) => { dragging = false; });
  set(50);
})();

// UTC clock
(function () {
  const el = document.getElementById('utcClock');
  if (!el) return;
  function tick() { el.textContent = 'UTC ' + new Date().toISOString().slice(11, 19); }
  tick(); setInterval(tick, 1000);
})();

// ── Live Scan · FastAPI integration ──────────────────────────────
;(function () {

const API = 'http://localhost:8000/api';
const COLORS = {
  deforestation:'hsl(142,76%,52%)', urban_expansion:'hsl(186,100%,58%)',
  flood:'hsl(210,100%,64%)', wildfire:'hsl(0,85%,62%)',
  glacial_retreat:'hsl(270,76%,68%)', agricultural:'hsl(35,100%,62%)',
  coastline:'hsl(195,80%,56%)', unknown:'hsl(186,12%,46%)',
};
const ICONS = {
  deforestation:'🌲', urban_expansion:'🏙', flood:'🌊', wildfire:'🔥',
  glacial_retreat:'🏔', agricultural:'🌾', coastline:'🏖', unknown:'?',
};

// API status pill
async function checkApi() {
  const el = document.getElementById('scanApiStatus');
  if (!el) return;
  try {
    const r = await fetch(API + '/health', { signal: AbortSignal.timeout(2500) });
    if (r.ok) { el.textContent = '● API ONLINE'; el.classList.remove('demo'); }
    else throw 0;
  } catch {
    el.textContent = '● DEMO MODE';
    el.classList.add('demo');
  }
}
checkApi();

// Preset wiring
document.getElementById('scanPreset')?.addEventListener('change', function () {
  if (!this.value) return;
  const [a,b,c,d] = this.value.split(',');
  document.getElementById('scanMinLon').value = a;
  document.getElementById('scanMinLat').value = b;
  document.getElementById('scanMaxLon').value = c;
  document.getElementById('scanMaxLat').value = d;
});

// Simulate result when API offline
function simulate(p) {
  const nd = (Math.random() - 0.4) * 0.7;
  const nw = (Math.random() - 0.4) * 0.4;
  const thr = 0.08 * (1.5 - p.sensitivity);
  const changes = [];
  if (nd < -thr) {
    const ct = Math.abs(nd) > 0.25 ? 'wildfire' : nw > 0.05 ? 'flood' : 'deforestation';
    changes.push({ change_type:ct, confidence:Math.min(0.97,Math.abs(nd)*2.8),
      area_km2:(Math.abs(nd)*280+5).toFixed(1) });
  }
  if (nd < -thr*0.6 && nw < -0.02)
    changes.push({ change_type:'urban_expansion', confidence:Math.min(0.90,Math.abs(nd)*2.1),
      area_km2:(Math.abs(nd)*110+3).toFixed(1) });
  if (!changes.length)
    changes.push({ change_type:'unknown', confidence:0.40, area_km2:'4.2' });
  const pct = Math.min(100, Math.abs(nd)*150 + Math.abs(nw)*80 + Math.random()*5);
  return {
    request_id: Math.random().toString(36).substr(2,8).toUpperCase(),
    ndvi_delta: +nd.toFixed(4), ndwi_delta: +nw.toFixed(4),
    change_percentage: +pct.toFixed(1),
    detected_changes: changes,
    ai_summary: `Analysis of ${p.source} imagery (${p.date_before} → ${p.date_after}) `
      + `identified ${changes.map(c=>c.change_type.replace(/_/g,' ')).join(', ')} `
      + `across ${pct.toFixed(1)}% of the AOI. ΔNDVI ${nd>=0?'+':''}${nd.toFixed(3)}, `
      + `ΔNDWI ${nw>=0?'+':''}${nw.toFixed(3)}. Peak confidence `
      + `${(Math.max(...changes.map(c=>c.confidence))*100).toFixed(0)}%. `
      + `(Demo mode — start FastAPI server for Claude AI narratives.)`,
    processing_time_ms: Math.round(Math.random()*1400+700),
  };
}

window.runScan = async function () {
  const btn = document.getElementById('scanBtn');
  const lbl = document.getElementById('scanBtnLabel');
  btn.disabled = true;
  lbl.innerHTML = '<span class="scan-spinner"></span>Processing…';
  document.getElementById('scanEmpty').style.display = 'flex';
  document.getElementById('scanOutput').style.display = 'none';

  const payload = {
    bbox: {
      min_lon: parseFloat(document.getElementById('scanMinLon').value),
      min_lat: parseFloat(document.getElementById('scanMinLat').value),
      max_lon: parseFloat(document.getElementById('scanMaxLon').value),
      max_lat: parseFloat(document.getElementById('scanMaxLat').value),
    },
    date_before: document.getElementById('scanDateBefore').value,
    date_after:  document.getElementById('scanDateAfter').value,
    source:          document.getElementById('scanSource').value,
    cloud_cover_max: parseInt(document.getElementById('scanCloud').value),
    sensitivity:     parseFloat(document.getElementById('scanSens').value),
  };

  let result;
  try {
    const resp = await fetch(API + '/analysis/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(15000),
    });
    if (!resp.ok) throw 0;
    result = await resp.json();
  } catch {
    await new Promise(r => setTimeout(r, 950));
    result = simulate(payload);
  }

  render(result);
  btn.disabled = false;
  lbl.innerHTML = '<span aria-hidden="true">▶</span>&nbsp; Initiate scan';
};

function render(r) {
  document.getElementById('scanEmpty').style.display  = 'none';
  const out = document.getElementById('scanOutput');
  out.style.display = 'flex';

  document.getElementById('scanRid').textContent = 'ID · ' + r.request_id;
  document.getElementById('scanMs').textContent  = r.processing_time_ms + ' ms';

  // KPIs
  const ndviEl = document.getElementById('smNdvi');
  const ndwiEl = document.getElementById('smNdwi');
  const pctEl  = document.getElementById('smChangePct');

  pctEl.textContent  = r.change_percentage.toFixed(1) + '%';
  pctEl.style.color  = 'var(--primary)';

  ndviEl.textContent = (r.ndvi_delta >= 0 ? '+' : '') + r.ndvi_delta.toFixed(3);
  ndviEl.style.color = r.ndvi_delta < -0.05 ? 'var(--alert)'
                     : r.ndvi_delta >  0.05 ? 'var(--signal)' : 'var(--foreground)';
  ndviEl.style.textShadow = 'none';

  ndwiEl.textContent = (r.ndwi_delta >= 0 ? '+' : '') + r.ndwi_delta.toFixed(3);
  ndwiEl.style.color = r.ndwi_delta >  0.05 ? 'var(--primary)'
                     : r.ndwi_delta < -0.05 ? 'var(--alert)'  : 'var(--foreground)';
  ndwiEl.style.textShadow = 'none';

  // Changes
  document.getElementById('scanChanges').innerHTML = r.detected_changes.map(c => {
    const col = COLORS[c.change_type] || '#888';
    const ico = ICONS[c.change_type]  || '?';
    const pct = (c.confidence * 100).toFixed(0);
    return `<div class="scan-change-item">
      <div class="scan-change-icon" style="background:${col}15;border-color:${col}30">${ico}</div>
      <div class="scan-change-info">
        <div class="scan-change-type" style="color:${col}">${c.change_type.replace(/_/g,' ')}</div>
        <div class="scan-conf-track">
          <div class="scan-conf-fill" style="width:0%;background:${col}" data-w="${pct}"></div>
        </div>
      </div>
      <div class="scan-change-stats">
        <div class="scan-conf-pct" style="color:${col}">${pct}%</div>
        <div class="scan-area">${parseFloat(c.area_km2).toFixed(0)} km²</div>
      </div>
    </div>`;
  }).join('');

  // Animate bars after paint
  requestAnimationFrame(() => requestAnimationFrame(() => {
    document.querySelectorAll('.scan-conf-fill[data-w]').forEach(el => {
      el.style.width = el.dataset.w + '%';
    });
  }));

  document.getElementById('scanAiText').textContent = r.ai_summary;
}

})();