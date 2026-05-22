/* proxmox.js — Dashboard Proxmox
   Polling toutes les 5 s vers /api/proxmox/stats
*/

const POLL_INTERVAL = 5000;

/* ── Utilitaires ── */
const $ = id => document.getElementById(id);
const fmt = (n, d = 1) => (typeof n === 'number' ? n.toFixed(d) : '—');
const toGo = bytes => (bytes / 1073741824).toFixed(1);
const toMo = bytes => (bytes / 1048576).toFixed(0);

function clamp(v, lo, hi) { return Math.min(Math.max(v, lo), hi); }

function gaugeColor(pct) {
  if (pct >= 90) return 'danger';
  if (pct >= 70) return 'warn';
  return '';
}

function tempClass(t) {
  if (t >= 85) return 'hot';
  if (t >= 65) return 'warn';
  return 'ok';
}

function setBar(el, pct) {
  if (!el) return;
  const p = clamp(pct, 0, 100);
  el.style.width = p + '%';
  el.className = 'px-gauge__fill ' + gaugeColor(p);
}

function formatUptime(seconds) {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const parts = [];
  if (d) parts.push(d + 'j');
  if (h) parts.push(h + 'h');
  parts.push(m + 'min');
  return parts.join(' ');
}

function formatBytes(bytes) {
  if (bytes >= 1e9)  return (bytes / 1e9).toFixed(1) + ' Go/s';
  if (bytes >= 1e6)  return (bytes / 1e6).toFixed(1) + ' Mo/s';
  if (bytes >= 1e3)  return (bytes / 1e3).toFixed(1) + ' Ko/s';
  return bytes + ' o/s';
}

function setStatus(online, text) {
  const el = $('px-status');
  el.className = 'px-status ' + (online ? 'px-status--online' : 'px-status--offline');
  el.querySelector('.px-status__text').textContent = text;
}

function setLastUpdate() {
  const now = new Date();
  $('px-last-update').textContent = now.toLocaleTimeString('fr-FR');
}

/* ── Render fonctions ── */
function renderTop(data) {
  /* CPU */
  const cpuPct = Math.round(data.cpu.percent);
  $('cpu-pct').textContent = cpuPct;
  setBar($('cpu-bar'), cpuPct);
  $('cpu-model').textContent = data.cpu.model || '—';
  $('cpu-cores').textContent = `${data.cpu.physical_cores} cœurs · ${data.cpu.logical_cores} threads`;

  /* RAM */
  const ramUsed = parseFloat(toGo(data.memory.used));
  const ramTotal = parseFloat(toGo(data.memory.total));
  const ramPct = data.memory.percent;
  $('ram-used').textContent = fmt(ramUsed);
  setBar($('ram-bar'), ramPct);
  $('ram-detail').textContent = `${toGo(data.memory.used)} / ${toGo(data.memory.total)} Go`;
  $('ram-pct').textContent = fmt(ramPct, 1) + '%';

  /* Swap */
  const swapPct = data.swap.percent;
  $('swap-used').textContent = toGo(data.swap.used);
  setBar($('swap-bar'), swapPct);
  $('swap-detail').textContent = `${toGo(data.swap.used)} / ${toGo(data.swap.total)} Go`;
  $('swap-pct').textContent = fmt(swapPct, 1) + '%';

  /* Uptime */
  $('uptime-val').textContent = formatUptime(data.uptime.seconds);
  $('uptime-since').textContent = 'Démarré le ' + data.uptime.boot_time;
}

function renderTemps(temps) {
  const container = $('px-temps');
  if (!temps || Object.keys(temps).length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.8rem">Aucune donnée de température disponible.</p>';
    return;
  }
  container.innerHTML = '';
  for (const [name, info] of Object.entries(temps)) {
    const t = info.current;
    const max = info.high || 100;
    const pct = clamp(Math.round((t / max) * 100), 0, 100);
    const cls = tempClass(t);
    const card = document.createElement('div');
    card.className = 'px-temp-card';
    card.innerHTML = `
      <span class="px-temp-card__name">${name}</span>
      <span class="px-temp-card__val ${cls}">${fmt(t, 1)}°C</span>
      <div class="px-gauge"><div class="px-gauge__fill ${cls === 'warn' ? 'warn' : cls === 'hot' ? 'danger' : ''}" style="width:${pct}%"></div></div>
      <span style="font-size:.68rem;color:var(--muted)">max ${info.high ? info.high + '°C' : '—'} · crit ${info.critical ? info.critical + '°C' : '—'}</span>
    `;
    container.appendChild(card);
  }
}

function renderStorage(disks) {
  const container = $('px-storage');
  if (!disks || disks.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.8rem">Aucun disque trouvé.</p>';
    return;
  }
  container.innerHTML = '';
  for (const disk of disks) {
    const pct = disk.percent;
    const row = document.createElement('div');
    row.className = 'px-storage-row';
    row.innerHTML = `
      <span class="px-storage-row__name">${disk.mountpoint} <span style="font-size:.68rem;color:var(--muted);font-weight:400">${disk.device}</span></span>
      <div class="px-storage-row__bar-wrap">
        <div class="px-gauge"><div class="px-gauge__fill ${gaugeColor(pct)}" style="width:${pct}%"></div></div>
      </div>
      <span class="px-storage-row__detail">${toGo(disk.used)} / ${toGo(disk.total)} Go · libre ${toGo(disk.free)} Go</span>
      <span class="px-storage-row__pct">${fmt(pct, 1)}%</span>
    `;
    container.appendChild(row);
  }
}

function renderNetwork(nets) {
  const container = $('px-net');
  if (!nets || Object.keys(nets).length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.8rem">Aucune interface réseau.</p>';
    return;
  }
  container.innerHTML = '';
  for (const [iface, info] of Object.entries(nets)) {
    const row = document.createElement('div');
    row.className = 'px-net-row';
    row.innerHTML = `
      <span class="px-net-row__iface">${iface}</span>
      <span class="px-net-row__rx">↓ ${formatBytes(info.bytes_recv_rate || 0)}</span>
      <span class="px-net-row__tx">↑ ${formatBytes(info.bytes_sent_rate || 0)}</span>
    `;
    container.appendChild(row);
  }
}

function renderVMs(vms) {
  const container = $('px-vms');
  if (!vms || vms.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.8rem">Aucun conteneur / VM trouvé.</p>';
    return;
  }
  container.innerHTML = '';
  for (const vm of vms) {
    const statusCls = vm.status === 'running' ? 'running' : vm.status === 'paused' ? 'paused' : 'stopped';
    const statusLabel = { running: 'Actif', stopped: 'Arrêté', paused: 'Suspendu' }[vm.status] || vm.status;
    const row = document.createElement('div');
    row.className = 'px-vm-row';
    row.innerHTML = `
      <span class="px-vm-row__name">${vm.name} <span class="px-vm-row__type">${vm.type}</span></span>
      <span class="px-vm-row__status ${statusCls}">${statusLabel}</span>
    `;
    container.appendChild(row);
  }
}

function renderSysInfo(info) {
  const container = $('px-info-list');
  const entries = [
    ['Hostname',       info.hostname],
    ['Système',        info.os],
    ['Noyau',          info.kernel],
    ['Architecture',   info.arch],
    ['Python',         info.python_version],
    ['Adresse IP',     info.ip_address],
    ['Processeur',     info.cpu_model],
    ['PID count',      info.pid_count],
    ['Load avg (1m)',  info.load_avg ? fmt(info.load_avg[0], 2) : '—'],
    ['Load avg (5m)',  info.load_avg ? fmt(info.load_avg[1], 2) : '—'],
    ['Load avg (15m)', info.load_avg ? fmt(info.load_avg[2], 2) : '—'],
  ];
  container.innerHTML = entries.map(([k, v]) => `
    <div class="px-info-item">
      <span>${k}</span>
      <span>${v || '—'}</span>
    </div>
  `).join('');
}

/* ── Fetch & poll ── */
async function fetchStats() {
  try {
    const res = await fetch('/api/proxmox/stats');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();

    setStatus(true, 'En ligne');
    setLastUpdate();

    renderTop(data);
    renderTemps(data.temperatures);
    renderStorage(data.disks);
    renderNetwork(data.network);
    renderVMs(data.vms);
    renderSysInfo(data.system);

  } catch (err) {
    setStatus(false, 'Hors ligne');
    console.error('[proxmox] Erreur fetch:', err);
  }
}

/* ── Bouton refresh ── */
$('px-refresh-btn').addEventListener('click', () => {
  const btn = $('px-refresh-btn');
  btn.classList.add('spinning');
  fetchStats().finally(() => {
    setTimeout(() => btn.classList.remove('spinning'), 700);
  });
});

/* ── Init ── */
fetchStats();
setInterval(fetchStats, POLL_INTERVAL);