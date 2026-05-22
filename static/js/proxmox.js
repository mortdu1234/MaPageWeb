/* proxmox.js — Dashboard Proxmox (données via API Proxmox)
   Polling toutes les 5 s vers /api/proxmox/stats
*/

const POLL_INTERVAL = 5000;

const $  = id => document.getElementById(id);
const fmt = (n, d = 1) => (typeof n === 'number' ? n.toFixed(d) : '—');

function toGo(bytes) {
  if (!bytes) return '0';
  return (bytes / 1073741824).toFixed(1);
}

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
  el.className   = 'px-gauge__fill ' + gaugeColor(p);
}

function formatUptime(s) {
  if (!s) return '—';
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const parts = [];
  if (d) parts.push(d + 'j');
  if (h) parts.push(h + 'h');
  parts.push(m + 'min');
  return parts.join(' ');
}

function formatBytes(b) {
  if (!b && b !== 0) return '—';
  for (const [u, lim] of [['o/s',1024],['Ko/s',1024],['Mo/s',1024],['Go/s',Infinity]]) {
    if (b < lim) return b.toFixed(1) + ' ' + u;
    b /= 1024;
  }
}

function setStatus(online, text) {
  const el = $('px-status');
  el.className = 'px-status ' + (online ? 'px-status--online' : 'px-status--offline');
  el.querySelector('.px-status__text').textContent = text;
}

function setLastUpdate() {
  $('px-last-update').textContent = new Date().toLocaleTimeString('fr-FR');
}

/* ── Render ── */

function renderTop(data) {
  // CPU
  const cpuPct = data.cpu.percent;
  $('cpu-pct').textContent   = fmt(cpuPct, 1);
  setBar($('cpu-bar'), cpuPct);
  $('cpu-model').textContent = data.cpu.model || '—';
  $('cpu-cores').textContent =
    `${data.cpu.sockets} socket(s) · ${data.cpu.physical_cores} cœurs · ${data.cpu.mhz ? data.cpu.mhz + ' MHz' : ''}`;

  // RAM
  const ramPct  = data.memory.percent;
  $('ram-used').textContent   = toGo(data.memory.used);
  setBar($('ram-bar'), ramPct);
  $('ram-detail').textContent = `${toGo(data.memory.used)} / ${toGo(data.memory.total)} Go`;
  $('ram-pct').textContent    = fmt(ramPct, 1) + '%';

  // Swap
  const swapPct  = data.swap.percent;
  $('swap-used').textContent   = toGo(data.swap.used);
  setBar($('swap-bar'), swapPct);
  $('swap-detail').textContent = `${toGo(data.swap.used)} / ${toGo(data.swap.total)} Go`;
  $('swap-pct').textContent    = fmt(swapPct, 1) + '%';

  // Uptime
  $('uptime-val').textContent   = data.uptime.human || formatUptime(data.uptime.seconds);
  $('uptime-since').textContent = data.load_avg
    ? `Load avg : ${data.load_avg.map(v => v.toFixed(2)).join(' · ')}`
    : '—';
}

function renderTemps(temps) {
  const container = $('px-temps');
  if (!temps || Object.keys(temps).length === 0) {
    container.innerHTML =
      '<p style="color:var(--muted);font-size:.8rem;grid-column:1/-1">' +
      'Aucune donnée de température — installez <code>lm-sensors</code> sur le nœud Proxmox.</p>';
    return;
  }
  container.innerHTML = '';
  for (const [name, info] of Object.entries(temps)) {
    const t   = info.current;
    const max = info.high || 100;
    const pct = clamp(Math.round(t / max * 100), 0, 100);
    const cls = tempClass(t);
    const gCls = cls === 'warn' ? 'warn' : cls === 'hot' ? 'danger' : '';
    const card = document.createElement('div');
    card.className = 'px-temp-card';
    card.innerHTML = `
      <span class="px-temp-card__name">${name}</span>
      <span class="px-temp-card__val ${cls}">${fmt(t, 1)}°C</span>
      <div class="px-gauge"><div class="px-gauge__fill ${gCls}" style="width:${pct}%"></div></div>
      <span style="font-size:.68rem;color:var(--muted)">
        max ${info.high ? info.high + '°C' : '—'} · crit ${info.critical ? info.critical + '°C' : '—'}
      </span>`;
    container.appendChild(card);
  }
}

function renderStorage(storage) {
  const container = $('px-storage');
  if (!storage || storage.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.8rem">Aucun stockage Proxmox trouvé.</p>';
    return;
  }
  container.innerHTML = '';
  for (const s of storage) {
    const pct = s.percent;
    const row = document.createElement('div');
    row.className = 'px-storage-row';
    row.innerHTML = `
      <div class="px-storage-row__info">
        <span class="px-storage-row__name">${s.storage}</span>
        <span class="px-storage-row__type">${s.type}</span>
      </div>
      <div class="px-storage-row__bar-wrap">
        <div class="px-gauge"><div class="px-gauge__fill ${gaugeColor(pct)}" style="width:${pct}%"></div></div>
      </div>
      <span class="px-storage-row__detail">${toGo(s.used)} / ${toGo(s.total)} Go</span>
      <span class="px-storage-row__pct">${fmt(pct, 1)}%</span>`;
    container.appendChild(row);
  }
}

function renderDisks(disks) {
  const container = $('px-disks');
  if (!disks || disks.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.8rem">Aucun disque physique détecté.</p>';
    return;
  }
  container.innerHTML = '';
  for (const d of disks) {
    const sizeGo = toGo(d.size);
    const typeIcon = d.type === 'ssd' || d.type === 'nvme' ? '⚡' : '💿';
    const health = d.health === 'PASSED' ? 'ok' : d.health === 'FAILED' ? 'hot' : '';
    const row = document.createElement('div');
    row.className = 'px-disk-row';
    row.innerHTML = `
      <span class="px-disk-row__dev">${typeIcon} ${d.devpath}</span>
      <span class="px-disk-row__model">${d.model || '—'}</span>
      <span class="px-disk-row__size">${sizeGo} Go</span>
      <span class="px-disk-row__type">${d.type || '—'}</span>
      <span class="px-disk-row__health ${health}">${d.health || '—'}</span>
      ${d.wearout != null ? `<span class="px-disk-row__wear">Usure : ${d.wearout}%</span>` : ''}`;
    container.appendChild(row);
  }
}

function renderNetwork(ifaces) {
  const container = $('px-net');
  if (!ifaces || ifaces.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.8rem">Aucune interface réseau.</p>';
    return;
  }
  container.innerHTML = '';
  for (const iface of ifaces) {
    const row = document.createElement('div');
    row.className = 'px-net-row';
    row.innerHTML = `
      <span class="px-net-row__iface">${iface.iface}</span>
      <span class="px-net-row__type">${iface.type}</span>
      <span class="px-net-row__addr">${iface.address || '—'}</span>
      <span class="px-net-row__state ${iface.active ? 'running' : 'stopped'}">${iface.active ? 'Actif' : 'Inactif'}</span>`;
    container.appendChild(row);
  }
}

function renderVMs(vms) {
  const container = $('px-vms');
  if (!vms || vms.length === 0) {
    container.innerHTML = '<p style="color:var(--muted);font-size:.8rem">Aucun conteneur / VM.</p>';
    return;
  }
  container.innerHTML = '';
  for (const vm of vms) {
    const statusCls   = vm.status === 'running' ? 'running' : vm.status === 'paused' ? 'paused' : 'stopped';
    const statusLabel = { running: 'Actif', stopped: 'Arrêté', paused: 'Suspendu' }[vm.status] || vm.status;
    const row = document.createElement('div');
    row.className = 'px-vm-row';

    const cpuBar  = vm.status === 'running' ? `<div class="px-gauge" style="width:80px"><div class="px-gauge__fill ${gaugeColor(vm.cpu)}" style="width:${clamp(vm.cpu,0,100)}%"></div></div>` : '';
    const memBar  = vm.status === 'running' ? `<div class="px-gauge" style="width:80px"><div class="px-gauge__fill ${gaugeColor(vm.mem_pct)}" style="width:${clamp(vm.mem_pct,0,100)}%;background:var(--ram-c)"></div></div>` : '';

    row.innerHTML = `
      <div class="px-vm-row__left">
        <span class="px-vm-row__name">${vm.name}</span>
        <span class="px-vm-row__type">${vm.type} #${vm.vmid}</span>
      </div>
      <div class="px-vm-row__metrics">
        ${vm.status === 'running' ? `
          <span class="px-vm-row__metric">CPU ${fmt(vm.cpu,1)}% ${cpuBar}</span>
          <span class="px-vm-row__metric">RAM ${toGo(vm.mem)}/${toGo(vm.maxmem)} Go ${memBar}</span>
          <span class="px-vm-row__metric">↑${vm.uptime}</span>
        ` : ''}
      </div>
      <span class="px-vm-row__status ${statusCls}">${statusLabel}</span>`;
    container.appendChild(row);
  }
}

function renderSysInfo(info) {
  const entries = [
    ['Hostname',      info.hostname],
    ['Version PVE',   info.pve_version],
    ['Release PVE',   info.pve_release],
    ['Noyau',         info.kernel],
    ['Processeur',    info.cpu_model],
    ['Sockets CPU',   info.cpu_sockets],
    ['Cœurs total',   info.cpu_cores],
    ['Architecture',  info.arch],
  ];
  $('px-info-list').innerHTML = entries.map(([k, v]) => `
    <div class="px-info-item">
      <span>${k}</span>
      <span>${v || '—'}</span>
    </div>`).join('');
}

function renderError(msg) {
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
  const banner = document.querySelector('.px-error-banner');
  if (banner) banner.classList.remove('visible');
}

/* ── Fetch & poll ── */

async function fetchStats() {
  try {
    const res = await fetch('/api/proxmox/stats');
    const data = await res.json();

    if (!res.ok || data.error) {
      setStatus(false, 'Erreur');
      renderError(data.error || `HTTP ${res.status}`);
      return;
    }

    clearError();
    setStatus(true, 'En ligne');
    setLastUpdate();

    renderTop(data);
    renderTemps(data.temperatures);
    renderStorage(data.storage);
    renderDisks(data.disks);
    renderNetwork(data.network);
    renderVMs(data.vms);
    renderSysInfo(data.system);

  } catch (err) {
    setStatus(false, 'Hors ligne');
    renderError('Impossible de joindre le serveur Flask.');
    console.error('[proxmox]', err);
  }
}

$('px-refresh-btn').addEventListener('click', () => {
  const btn = $('px-refresh-btn');
  btn.classList.add('spinning');
  fetchStats().finally(() => setTimeout(() => btn.classList.remove('spinning'), 700));
});

fetchStats();
setInterval(fetchStats, POLL_INTERVAL);