/* proxmox.js — Dashboard Proxmox */

const POLL_INTERVAL = 5000;
const DONUT_CIRC    = 2 * Math.PI * 48; // ~301.6

const $  = id => document.getElementById(id);
const fmt = (n, d = 1) => (typeof n === 'number' ? n.toFixed(d) : String(n ?? '—'));

function toGo(bytes) {
  if (!bytes && bytes !== 0) return '0';
  return (bytes / 1073741824).toFixed(1);
}

function clamp(v, lo, hi) { return Math.min(Math.max(v, lo), hi); }

function gaugeColor(pct) {
  if (pct >= 90) return 'danger';
  if (pct >= 70) return 'warn';
  return '';
}

function setBar(el, pct) {
  if (!el) return;
  const p = clamp(pct ?? 0, 0, 100);
  el.style.width = p + '%';
  el.className   = 'px-gauge__fill ' + gaugeColor(p);
}

function setStatus(online, text) {
  const el = $('px-status');
  el.className = 'px-status ' + (online ? 'px-status--online' : 'px-status--offline');
  el.querySelector('.px-status__text').textContent = text;
}

function setLastUpdate() {
  $('px-last-update').textContent = new Date().toLocaleTimeString('fr-FR');
}

function showError(msg) {
  let banner = document.querySelector('.px-error-banner');
  if (!banner) {
    banner = document.createElement('div');
    banner.className = 'px-error-banner';
    document.querySelector('.px-wrapper').prepend(banner);
  }
  banner.textContent = '⚠ ' + msg;
  banner.classList.add('visible');
}

function clearError() {
  const b = document.querySelector('.px-error-banner');
  if (b) b.classList.remove('visible');
}

/* ── Render ── */

function renderTop(data) {
  const cpuPct = data.cpu.percent;
  $('cpu-pct').textContent   = fmt(cpuPct, 1);
  setBar($('cpu-bar'), cpuPct);
  $('cpu-model').textContent = data.cpu.model || '—';
  $('cpu-cores').textContent =
    `${data.cpu.sockets} socket · ${data.cpu.physical_cores} cœurs · ${data.cpu.mhz ? Math.round(data.cpu.mhz) + ' MHz' : ''}`;

  const ramPct = data.memory.percent;
  $('ram-used').textContent   = toGo(data.memory.used);
  setBar($('ram-bar'), ramPct);
  $('ram-detail').textContent = `${toGo(data.memory.used)} / ${toGo(data.memory.total)} Go`;
  $('ram-pct').textContent    = fmt(ramPct, 1) + '%';

  const swapPct = data.swap.percent;
  $('swap-used').textContent   = toGo(data.swap.used);
  setBar($('swap-bar'), swapPct);
  $('swap-detail').textContent = `${toGo(data.swap.used)} / ${toGo(data.swap.total)} Go`;
  $('swap-pct').textContent    = fmt(swapPct, 1) + '%';

  $('uptime-val').textContent = data.uptime.human || '—';
  if (data.load_avg && data.load_avg.length) {
    $('uptime-since').textContent =
      'Load avg : ' + data.load_avg.map(v => parseFloat(v).toFixed(2)).join(' · ');
  }
}

function renderStorage(storage) {
  const container = $('px-storage');
  if (!storage || storage.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.82rem">Aucun stockage trouvé.</p>';
    return;
  }
  container.innerHTML = '';
  for (const s of storage) {
    const pct = s.percent ?? 0;
    const row = document.createElement('div');
    row.className = 'px-storage-row';
    row.innerHTML = `
      <div class="px-storage-row__info">
        <span class="px-storage-row__name">${s.storage}</span>
        <span class="px-storage-row__type">${s.type}</span>
      </div>
      <div class="px-storage-row__bar-wrap">
        <div class="px-gauge">
          <div class="px-gauge__fill ${gaugeColor(pct)}" style="width:${pct}%"></div>
        </div>
      </div>
      <span class="px-storage-row__detail">${toGo(s.used)} / ${toGo(s.total)} Go · libre ${toGo(s.avail)} Go</span>
      <span class="px-storage-row__pct">${fmt(pct, 1)}%</span>`;
    container.appendChild(row);
  }
}

/* ── Donuts disques ── */

function setDonut(arcId, pctId, metaId, cardId, disks, storage) {
  const arc    = $(arcId);
  const pctEl  = $(pctId);
  const metaEl = $(metaId);
  const card   = $(cardId);

  if (!disks || disks.length === 0) {
    card.classList.add('px-donut-empty');
    pctEl.textContent  = '—';
    metaEl.textContent = 'Aucun disque';
    arc.setAttribute('stroke-dasharray', `0 ${DONUT_CIRC}`);
    return;
  }

  card.classList.remove('px-donut-empty');

  // Calculer used/total réels depuis les données de stockage Proxmox
  // On agrège tous les stockages actifs dont le contenu inclut "images" ou "rootdir"
  let totalBytes = 0, usedBytes = 0;
  if (storage && storage.length > 0) {
    for (const s of storage) {
      totalBytes += s.total || 0;
      usedBytes  += s.used  || 0;
    }
  }

  // Fallback : si pas de données stockage, afficher la taille brute des disques physiques
  if (totalBytes === 0) {
    totalBytes = disks.reduce((s, d) => s + (d.size || 0), 0);
    usedBytes  = 0;
  }

  const pct = totalBytes > 0 ? clamp(Math.round(usedBytes / totalBytes * 100), 0, 100) : 0;

  const dash = (pct / 100 * DONUT_CIRC).toFixed(1);
  arc.setAttribute('stroke-dasharray', `${dash} ${DONUT_CIRC}`);
  arc.classList.toggle('danger', pct >= 90);

  pctEl.textContent = pct + '%';

  const totalGo = (totalBytes / 1073741824).toFixed(1);
  const usedGo  = (usedBytes  / 1073741824).toFixed(1);
  const names   = disks.map(d => d.devpath).join(', ');
  metaEl.innerHTML = `
    <strong>${disks.length} disque${disks.length > 1 ? 's' : ''}</strong> · ${usedGo} / ${totalGo} Go<br>
    <span style="font-family:monospace;font-size:.72rem">${names}</span>`;
}

function renderDisks(disks, storage) {
  const container = $('px-disks');
  if (!disks || disks.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.82rem">Aucun disque physique détecté.</p>';
    renderDonuts([], storage);
    return;
  }

  window._allDiskTotal = disks.reduce((s, d) => s + (d.size || 0), 0) || 1;

  renderDonuts(disks, storage);

  container.innerHTML = '';
  for (const d of disks) {
    const typeIcon  = d.type === 'ssd' ? '⚡ SSD' : d.type === 'nvme' ? '⚡ NVMe' : '💿 HDD';
    const healthCls = d.health === 'PASSED' ? 'ok' : d.health === 'FAILED' ? 'hot' : '';
    const wearTxt   = d.wearout != null && d.wearout !== 'N/A'
      ? `<span class="px-disk-row__wear">Usure : ${d.wearout}%</span>` : '';
    const rpmTxt    = d.rpm && d.rpm !== 0
      ? `<span style="font-size:.7rem;color:var(--muted)">${d.rpm} tr/min</span>` : '';
    const row = document.createElement('div');
    row.className = 'px-disk-row';
    row.innerHTML = `
      <span class="px-disk-row__dev">${d.devpath}</span>
      <span class="px-disk-row__model">${(d.model || '—').replace(/_/g,' ')}</span>
      <span class="px-disk-row__size">${toGo(d.size)} Go</span>
      <span class="px-disk-row__type">${typeIcon}</span>
      ${rpmTxt}
      <span class="px-disk-row__health ${healthCls}">${d.health || '—'}</span>
      ${wearTxt}`;
    container.appendChild(row);
  }
}

function renderDonuts(disks, storage) {
  const hdds = disks.filter(d => d.type === 'hdd');
  const ssds  = disks.filter(d => d.type === 'ssd' || d.type === 'nvme');

  // Séparer les stockages par type de disque (heuristique sur le nom/type)
  // Pour les HDD : stockages de type lvm, dir sur des HDD
  // Pour les SSD : stockages sur le SSD (pve, local-lvm, etc.)
  // On fait simple : on passe tous les stockages aux deux donuts,
  // chaque donut affiche used/total de ses disques physiques associés
  const hddStorage = storage ? storage.filter(s =>
    s.type === 'lvm' || s.type === 'lvmthin' || s.type === 'dir'
  ) : [];
  const ssdStorage = storage ? storage.filter(s =>
    s.storage === 'local' || s.storage === 'local-lvm' || s.type === 'zfspool'
  ) : [];

  setDonut('donut-hdd-arc', 'donut-hdd-pct', 'donut-hdd-meta', 'px-donut-hdd', hdds, hddStorage);
  setDonut('donut-ssd-arc', 'donut-ssd-pct', 'donut-ssd-meta', 'px-donut-ssd', ssds, ssdStorage);
}

/* ── Fetch ── */

async function fetchStats() {
  try {
    const res  = await fetch('/api/proxmox/stats');
    const data = await res.json();

    if (!res.ok || data.error) {
      setStatus(false, 'Erreur API');
      showError(data.error || `HTTP ${res.status}`);
      return;
    }

    clearError();
    setStatus(true, 'En ligne');
    setLastUpdate();

    renderTop(data);
    renderStorage(data.storage);
    renderDisks(data.disks, data.storage);

  } catch (err) {
    setStatus(false, 'Hors ligne');
    showError(`Fetch échoué : ${err.message}`);
    console.error('[proxmox]', err);
  }
}

$('px-refresh-btn').addEventListener('click', () => {
  const btn = $('px-refresh-btn');
  btn.classList.add('spinning');
  fetchStats().finally(() => setTimeout(() => btn.classList.remove('spinning'), 700));
});

fetchStats();