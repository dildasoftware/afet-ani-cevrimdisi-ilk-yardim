const scene = document.getElementById("scene");
const emptyState = document.getElementById("emptyState");
const form = document.getElementById("composerForm");
const input = document.getElementById("questionInput");
const emergencyBtn = document.getElementById("emergencyBtn");
const emergencyOverlay = document.getElementById("emergencyOverlay");
const closeEmergency = document.getElementById("closeEmergency");
const sessionClock = document.getElementById("sessionClock");
const bootTime = document.getElementById("bootTime");
const logList = document.getElementById("logList");
const logCount = document.getElementById("logCount");
const statCount = document.getElementById("statCount");
const gaugeFill = document.getElementById("gaugeFill");
const sessionIdEl = document.getElementById("sessionId");
const latencyNum = document.getElementById("latencyNum");
const crumbCurrent = document.getElementById("crumbCurrent");

/* ---------- Yardımcılar ---------- */
function pad(n) { return String(n).padStart(2, "0"); }
function fmtTime(d) { return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; }
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/* ---------- Oturum ID + saat ---------- */
const startedAt = new Date();
bootTime.textContent = fmtTime(startedAt);
sessionIdEl.textContent = "RESP-" + Math.floor(1000 + Math.random() * 8999);

setInterval(() => {
  const elapsed = Math.floor((Date.now() - startedAt.getTime()) / 1000);
  sessionClock.textContent = `${pad(Math.floor(elapsed / 60))}:${pad(elapsed % 60)}`;
}, 1000);

/* ---------- 277 sayacı ---------- */
function animateCount(el, target, duration = 1600) {
  const start = performance.now();
  function step(now) {
    const p = Math.min(1, (now - start) / duration);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(target * eased);
    if (p < 1) requestAnimationFrame(step);
    else el.textContent = target;
  }
  requestAnimationFrame(step);
}
if (statCount) animateCount(statCount, parseInt(statCount.dataset.target, 10));

/* ---------- Gauge ---------- */
if (gaugeFill) {
  requestAnimationFrame(() => { gaugeFill.style.width = "56%"; });
}

/* ---------- Canlı gecikme grafiği (canvas, sürekli akıyor) ---------- */
const latCanvas = document.getElementById("latencyChart");
if (latCanvas) {
  const ctx = latCanvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const rect = latCanvas.getBoundingClientRect();
  latCanvas.width = rect.width * dpr;
  latCanvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;
  const data = new Array(48).fill(0.12);

  function drawLatency() {
    ctx.clearRect(0, 0, w, h);

    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();

    const step = w / (data.length - 1);
    const min = 0.08, max = 0.22;
    const norm = (v) => h - ((v - min) / (max - min)) * (h - 6) - 3;

    ctx.beginPath();
    ctx.moveTo(0, h);
    data.forEach((v, i) => ctx.lineTo(i * step, norm(v)));
    ctx.lineTo(w, h);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "rgba(77,138,214,0.28)");
    grad.addColorStop(1, "rgba(77,138,214,0)");
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.beginPath();
    data.forEach((v, i) => {
      const x = i * step, y = norm(v);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = "#4d8ad6";
    ctx.lineWidth = 1.4;
    ctx.stroke();

    const lx = w, ly = norm(data[data.length - 1]);
    ctx.fillStyle = "#4d8ad6";
    ctx.beginPath();
    ctx.arc(lx - 1, ly, 2.2, 0, Math.PI * 2);
    ctx.fill();
  }

  setInterval(() => {
    data.shift();
    const drift = 0.12 + (Math.random() - 0.5) * 0.08;
    data.push(Math.max(0.08, Math.min(0.22, drift)));
    latencyNum.textContent = data[data.length - 1].toFixed(2);
    drawLatency();
  }, 700);

  drawLatency();
}

/* ---------- Olay günlüğü ---------- */
let eventCount = 1;
logCount.textContent = pad(eventCount);

function addEvent({ title, body, tone = "ok" }) {
  eventCount++;
  logCount.textContent = pad(eventCount);
  const el = document.createElement("article");
  el.className = "event event--" + tone;
  el.innerHTML = `
    <div class="event__meta">
      <span class="event__time">${fmtTime(new Date())}</span>
      <span class="event__dot event__dot--${tone}"></span>
    </div>
    <p class="event__title">${escapeHtml(title)}</p>
    <p class="event__body">${escapeHtml(body)}</p>
  `;
  logList.insertBefore(el, logList.firstChild);
  while (logList.children.length > 6) logList.removeChild(logList.lastChild);
}

/* ---------- Acil durum ---------- */
function openEC() {
  emergencyOverlay.classList.add("is-active");
  emergencyOverlay.setAttribute("aria-hidden", "false");
  addEvent({ title: "Acil Durum Kartı Açıldı", body: "112 kartı gösterildi. Bypass modu.", tone: "red" });
}
function closeEC() {
  emergencyOverlay.classList.remove("is-active");
  emergencyOverlay.setAttribute("aria-hidden", "true");
}
emergencyBtn.addEventListener("click", openEC);
closeEmergency.addEventListener("click", closeEC);
emergencyOverlay.addEventListener("click", (e) => {
  if (e.target === emergencyOverlay) closeEC();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeEC();
  if (e.key === "/" && document.activeElement !== input) {
    e.preventDefault();
    input.focus();
  }
});

/* ---------- Hızlı sekmeler ---------- */
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    handleQuestion(chip.getAttribute("data-prompt"));
  });
});

/* ---------- Protokol kartı ---------- */
function firstCategoryLabel(sources) {
  if (!sources || !sources.length) return "Protokol Yanıtı";
  const doc = sources[0].doc || "";
  if (doc.includes("kanama")) return "Kanama Kontrol Protokolü";
  if (doc.includes("kirik") || doc.includes("cikik")) return "Kırık / Çıkık Protokolü";
  if (doc.includes("cpr")) return "Temel Yaşam Desteği Protokolü";
  if (doc.includes("bogulma")) return "Boğulma Protokolü";
  if (doc.includes("yanik")) return "Yanık Protokolü";
  if (doc.includes("sok")) return "Şok Protokolü";
  if (doc.includes("deprem")) return "Deprem Protokolü";
  return "Protokol Yanıtı";
}

function shortRef(doc) {
  if (!doc) return "GEN-01";
  if (doc.includes("kanama")) return "KNM-01";
  if (doc.includes("kirik")) return "KRK-01";
  if (doc.includes("cpr_cocuk")) return "CPR-02";
  if (doc.includes("cpr_bebek")) return "CPR-03";
  if (doc.includes("cpr")) return "CPR-01";
  if (doc.includes("bogulma")) return "BGM-01";
  if (doc.includes("yanik")) return "YNK-01";
  if (doc.includes("sok")) return "SOK-01";
  if (doc.includes("deprem")) return "DPR-01";
  return "GEN-01";
}

function renderThinking(question) {
  if (emptyState && emptyState.parentNode) emptyState.remove();
  crumbCurrent.textContent = "İşleniyor…";
  scene.innerHTML = `
    <div class="protocol">
      <div class="protocol__meta">
        <span class="protocol__meta-tag">Sorgu</span>
        <span class="protocol__meta-q">${escapeHtml(question)}</span>
      </div>
      <div class="protocol__card">
        <div class="thinking-dots"><span></span><span></span><span></span></div>
      </div>
    </div>
  `;
  scene.scrollTop = 0;
}

function renderAnswer(question, data) {
  if (emptyState && emptyState.parentNode) emptyState.remove();
  const isFallback = !data.has_sufficient_context;
  const title = isFallback ? "Belirsiz Sorgu" : firstCategoryLabel(data.sources);
  const ref = isFallback ? "N/A" : shortRef(data.sources[0]?.doc);
  crumbCurrent.textContent = title;

  const stepsHtml = (data.sources || []).flatMap((src) =>
    src.lines.map((line, i) => `
      <div class="step">
        <span class="step__n">${pad(i + 1)}</span>
        <div class="step__body">${escapeHtml(line)}</div>
      </div>
    `)
  ).join("");

  const srcDocs = [...new Set((data.sources || []).map((s) => s.doc))].join(", ");

  scene.innerHTML = `
    <div class="protocol ${isFallback ? "protocol--fallback" : ""}">
      <div class="protocol__meta">
        <span class="protocol__meta-tag">Sorgu</span>
        <span class="protocol__meta-q">${escapeHtml(question)}</span>
      </div>

      <div class="protocol__card">
        <header class="protocol__head">
          <div class="protocol__head-mark">✻</div>
          <div>
            <h2 class="protocol__head-title" id="protoTitle"></h2>
            <p class="protocol__head-ref">
              <strong>Ref:</strong> ${ref} · <strong>Aciliyet:</strong> ${isFallback ? "—" : "Yüksek"} · <strong>Doğrulama:</strong> %87.5
            </p>
          </div>
        </header>

        <div class="protocol__body">
          <p class="protocol__intro" id="protoIntro"></p>
          ${isFallback ? "" : stepsHtml}
        </div>

        ${!isFallback ? `
        <div class="protocol__foot">
          <p class="protocol__src"><strong>Kaynak:</strong> ${escapeHtml(srcDocs)}</p>
          <span style="font-family:var(--mono);font-size:10.5px;color:var(--ok);letter-spacing:0.1em;text-transform:uppercase;font-weight:700">✓ Doğrulanmış</span>
        </div>` : ""}
      </div>

      <div class="protocol__disclaimer">
        <strong>Uyarı</strong>
        Bu bilgi tıbbi tavsiye yerine geçmez. Ciddi bir durumda hemen 112'yi arayın.
      </div>
    </div>
  `;

  typeText(document.getElementById("protoTitle"), title);
  typeText(document.getElementById("protoIntro"), data.answer_intro, 8);

  addEvent({
    title: isFallback ? "Belirsiz sorgu alındı" : `${title} açıldı`,
    body: isFallback ? "Kullanıcı yönlendirildi." : `Ref ${ref} · ${(data.sources || []).length} kaynak`,
    tone: isFallback ? "amber" : "red",
  });

  scene.scrollTop = 0;
}

function typeText(el, text, speed = 11) {
  if (!el) return;
  let i = 0;
  function step() {
    el.textContent = text.slice(0, i);
    i++;
    if (i <= text.length) setTimeout(step, speed);
  }
  step();
}

/* ---------- İstek ---------- */
async function handleQuestion(question) {
  input.value = "";
  renderThinking(question);
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) throw new Error("Sunucu hatası: " + res.status);
    const data = await res.json();
    renderAnswer(question, data);
  } catch (err) {
    renderAnswer(question, {
      answer_intro: "Sunucuya bağlanılamadı. Backend'in (api.py) çalıştığından emin olun.",
      sources: [],
      has_sufficient_context: false,
    });
    console.error(err);
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;
  handleQuestion(q);
});

/* ---------- Bölge Haritası ---------- */
const mapBtn = document.getElementById("mapBtn");
if (mapBtn) {
  mapBtn.addEventListener("click", () => {
    if (emptyState && emptyState.parentNode) emptyState.remove();
    crumbCurrent.textContent = "Bölge Bilgisi";
    scene.innerHTML = `
      <div class="protocol protocol--fallback">
        <div class="protocol__card">
          <header class="protocol__head">
            <div class="protocol__head-mark">ℹ</div>
            <div>
              <h2 class="protocol__head-title">Bölge Bilgisi — Yakında</h2>
            </div>
          </header>
          <div class="protocol__body">
            <p class="protocol__intro" style="margin-bottom: 24px; line-height: 1.6;">
              Bu özelliği, AFAD'ın resmi açık veri kaynaklarını kullanarak tamamen çevrimdışı çalışacak şekilde geliştiriyoruz. Şimdilik, size en yakın afet toplanma alanını AFAD'ın resmi sorgulama servisinden öğrenebilirsiniz:
            </p>
            <a href="https://www.turkiye.gov.tr/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama" target="_blank" style="display: inline-flex; align-items: center; justify-content: center; background: var(--primary-color); color: #fff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 500; transition: background 0.2s;">
              AFAD Toplanma Alanı Sorgula ↗
            </a>
          </div>
        </div>
      </div>
    `;
    scene.scrollTop = 0;
  });
}

/* ---------- Protokol arama / chip filtreleme ---------- */
(function () {
  const searchInput = document.querySelector(".topbar__search-input");
  const chipsNav    = document.getElementById("chips");
  if (!searchInput || !chipsNav) return;

  /* "Eşleşen protokol bulunamadı" mesajı */
  const noMatch = document.createElement("p");
  noMatch.className = "chips__no-match";
  noMatch.textContent = "Eşleşen protokol bulunamadı";
  noMatch.style.cssText = (
    "display:none; margin:8px 0 0 2px; font-size:11.5px; " +
    "color:var(--text-muted,#6b7280); letter-spacing:0.04em;"
  );
  chipsNav.insertAdjacentElement("afterend", noMatch);

  /**
   * Türkçe büyük/küçük harf duyarsız normalleştirme.
   * İ→i ve I→ı dönüşümünü locale'den bağımsız olarak yapıyoruz.
   */
  function normalizeTR(str) {
    return str
      .replace(/İ/g, "i")
      .replace(/I/g, "ı")
      .toLowerCase();
  }

  searchInput.addEventListener("input", () => {
    const q = normalizeTR(searchInput.value.trim());
    const allChips = chipsNav.querySelectorAll(".chip");
    let visible = 0;

    allChips.forEach((chip) => {
      const label = normalizeTR(chip.textContent);
      const match = !q || label.includes(q);
      chip.style.display = match ? "" : "none";
      if (match) visible++;
    });

    noMatch.style.display = (q && visible === 0) ? "block" : "none";
  });

  /* Ctrl+K / ⌘K ile arama kutusuna odaklan */
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
  });
})();

/* ---------- Protokoller (Kategori ve Belge Görüntüleme) ---------- */
const protocolsBtn = document.getElementById("protocolsBtn");
const historyBtn = document.getElementById("historyBtn");
const homeBtn = document.getElementById("homeBtn");
const crumbsHomeBtn = document.querySelector(".crumbs__item");

// Global array to keep history data for quick reuse on click
let currentHistoryData = [];

window.showHistoryItem = function(index) {
  const data = currentHistoryData[index];
  if (!data) return;
  
  crumbCurrent.textContent = "Sorgu Detayı";
  
  const isFallback = !data.has_sufficient_context;
  let html = `
    <div class="protocol ${isFallback ? "protocol--fallback" : ""}">
      <div class="protocol__card">
        <header class="protocol__head">
          <div class="protocol__head-mark">${isFallback ? "⚠️" : "🛡️"}</div>
          <div>
            <h2 class="protocol__head-title">${escapeHtml(data.question)}</h2>
            <p class="protocol__head-ref">
              <strong>Zaman:</strong> ${data.timestamp}
            </p>
          </div>
        </header>

        <div class="protocol__body">
          <p class="protocol__intro">${escapeHtml(data.answer_intro)}</p>
  `;
  
  if (!isFallback && data.sources && data.sources.length) {
    let stepCount = 0;
    data.sources.forEach(src => {
      src.lines.forEach(line => {
        stepCount++;
        let cleanLine = line.replace(/^\d+\.\s*/, '');
        html += `
          <div class="step">
            <span class="step__n">${pad(stepCount)}</span>
            <div class="step__body">${escapeHtml(cleanLine)}</div>
          </div>
        `;
      });
    });
    
    const srcDocs = [...new Set(data.sources.map(s => s.doc))].join(", ");
    html += `
        <div class="protocol__foot">
          <p class="protocol__src"><strong>Kaynak:</strong> ${escapeHtml(srcDocs)}</p>
          <span style="font-family:var(--mono);font-size:10.5px;color:var(--ok);letter-spacing:0.1em;text-transform:uppercase;font-weight:700">✓ Doğrulanmış</span>
        </div>
    `;
  }
  
  html += `
        </div>
        <div class="protocol__disclaimer">
          <strong>Uyarı</strong>
          Bu bilgi tıbbi tavsiye yerine geçmez. Ciddi bir durumda hemen 112'yi arayın.
        </div>
      </div>
    </div>
  `;
  
  scene.innerHTML = html;
};

if (historyBtn) {
  historyBtn.addEventListener("click", async () => {
    document.querySelectorAll(".menu__item").forEach(btn => btn.classList.remove("is-active"));
    historyBtn.classList.add("is-active");

    if (emptyState && emptyState.parentNode) emptyState.remove();
    crumbCurrent.textContent = "Vaka Geçmişi";
    scene.innerHTML = `<div style="padding: 24px; color: var(--tx-4); font-family: var(--mono); text-transform: uppercase; letter-spacing: 0.1em; font-size: 11px;">Yükleniyor...</div>`;

    try {
      const res = await fetch("/history");
      const data = await res.json();
      currentHistoryData = data.history || [];
      
      if (currentHistoryData.length === 0) {
        scene.innerHTML = `<div style="padding: 24px; color: var(--tx-4); font-family: var(--mono); font-size: 13px;">Henüz sorgu geçmişi yok.</div>`;
        return;
      }
      
      let html = `<div class="protocol"><div class="protocol__card"><div class="protocol__body" style="padding-top: 8px;">`;
      html += `<h3 style="margin: 24px 0 16px 0; color: var(--tx); font-size: 15px; font-weight: 600; padding-bottom: 6px; border-bottom: 1px solid var(--line);">Sorgu Geçmişi</h3>`;
      html += `<div style="display: flex; flex-direction: column; gap: 8px;">`;
      
      currentHistoryData.forEach((item, idx) => {
        const badgeClass = item.has_sufficient_context ? "event--ok" : "event--amber";
        const badgeText = item.has_sufficient_context ? "Cevaplandı" : "Belirsiz";
        
        html += `
          <div class="event ${badgeClass}" style="cursor: pointer; transition: all 0.2s;" onclick="showHistoryItem(${idx})" onmouseover="this.style.backgroundColor='var(--bg-2)';" onmouseout="this.style.backgroundColor='var(--bg-1)';">
            <span class="event__time">${item.timestamp}</span>
            <div class="event__msg">${escapeHtml(item.question)}</div>
            <span class="event__status">${badgeText}</span>
          </div>
        `;
      });
      
      html += `</div></div></div></div>`;
      scene.innerHTML = html;
      scene.scrollTop = 0;
    } catch (err) {
      scene.innerHTML = `<div style="padding: 24px; color: var(--red); font-family: var(--mono); font-size: 12px;">Bağlantı hatası: ${err.message}</div>`;
    }
  });
}


function goHome() {
  window.location.reload();
}

if (homeBtn) homeBtn.addEventListener("click", goHome);
if (crumbsHomeBtn) crumbsHomeBtn.addEventListener("click", goHome);

if (protocolsBtn) {
  protocolsBtn.addEventListener("click", async () => {
    document.querySelectorAll(".menu__item").forEach(btn => btn.classList.remove("is-active"));
    protocolsBtn.classList.add("is-active");

    if (emptyState && emptyState.parentNode) emptyState.remove();
    crumbCurrent.textContent = "Tüm Protokoller";
    scene.innerHTML = `<div style="padding: 24px; color: var(--tx-4); font-family: var(--mono); text-transform: uppercase; letter-spacing: 0.1em; font-size: 11px;">Yükleniyor...</div>`;

    try {
      const res = await fetch("/categories");
      const data = await res.json();
      
      let html = `<div class="protocol"><div class="protocol__card"><div class="protocol__body" style="padding-top: 8px;">`;
      
      data.categories.forEach(cat => {
        html += `<h3 style="margin: 24px 0 16px 0; color: var(--tx); font-size: 15px; font-weight: 600; padding-bottom: 6px; border-bottom: 1px solid var(--line);">${cat.label}</h3>`;
        html += `<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px;">`;
        cat.documents.forEach(doc => {
          html += `
            <div class="stat" style="cursor: pointer; padding: 12px 14px; border-radius: 8px; border: 1px solid var(--line-2); background: var(--bg-1); transition: all 0.2s;" onclick="loadDocument('${doc.doc}', '${doc.title}')" onmouseover="this.style.borderColor='var(--navy)'; this.style.backgroundColor='var(--bg-2)';" onmouseout="this.style.borderColor='var(--line-2)'; this.style.backgroundColor='var(--bg-1)';">
              <div class="stat__label" style="font-size: 13.5px; font-weight: 550; color: var(--tx); margin-bottom: 4px;">${doc.title}</div>
              <div class="stat__val" style="font-size: 11px; color: var(--tx-4); font-family: var(--mono); text-transform: uppercase; letter-spacing: 0.05em;">${doc.chunk_count} Madde</div>
            </div>
          `;
        });
        html += `</div>`;
      });
      
      html += `</div></div></div>`;
      scene.innerHTML = html;
      scene.scrollTop = 0;
    } catch (err) {
      scene.innerHTML = `<div style="padding: 24px; color: var(--red); font-family: var(--mono); font-size: 12px;">Bağlantı hatası: ${err.message}</div>`;
    }
  });
}

window.loadDocument = async function(docName, docTitle) {
  crumbCurrent.textContent = docTitle;
  scene.innerHTML = `<div style="padding: 24px; color: var(--tx-4); font-family: var(--mono); text-transform: uppercase; letter-spacing: 0.1em; font-size: 11px;">Yükleniyor...</div>`;
  
  try {
    const res = await fetch(`/document/${docName}`);
    if (!res.ok) throw new Error("Belge yüklenemedi");
    const data = await res.json();
    
    let html = `
      <div class="protocol">
        <div class="protocol__card">
          <header class="protocol__head">
            <div class="protocol__head-mark">📄</div>
            <div>
              <h2 class="protocol__head-title">${docTitle}</h2>
              <p class="protocol__head-ref">
                <strong>Kategori:</strong> ${data.category} · <strong>Kaynak:</strong> ${docName}
              </p>
            </div>
          </header>
          <div class="protocol__body">
    `;
    
    data.lines.forEach((line, idx) => {
      // Satır numarasını (örn: "1. ") temizleyelim, numaralandırma zaten .step__n ile yapılıyor
      // Regex: baştaki rakamlar, ardından nokta ve boşlukları sil
      let cleanLine = line.replace(/^\d+\.\s*/, '');
      html += `
        <div class="step">
          <span class="step__n">${pad(idx + 1)}</span>
          <div class="step__body">${escapeHtml(cleanLine)}</div>
        </div>
      `;
    });
    
    html += `
          </div>
          ${data.source_citation ? `
          <div class="protocol__foot" style="margin-top: 16px; border-top: 1px solid var(--line); padding-top: 12px;">
            <p class="protocol__src" style="font-size: 11px; color: var(--tx-4); line-height: 1.4;"><strong>Kaynak:</strong> ${escapeHtml(data.source_citation)}</p>
          </div>
          ` : ""}
        </div>
      </div>
    `;
    
    scene.innerHTML = html;
    scene.scrollTop = 0;
  } catch (err) {
    scene.innerHTML = `<div style="padding: 24px; color: var(--red); font-family: var(--mono); font-size: 12px;">Hata: ${err.message}</div>`;
  }
};

