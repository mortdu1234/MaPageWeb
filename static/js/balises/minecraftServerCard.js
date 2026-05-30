import { injectCSS } from './Utils.js';

class MinecraftServerCard extends HTMLElement {
    connectedCallback() {
        injectCSS('minecraft-server-card', 'minecraftServerCard.css');

        const serverID  = this.getAttribute('serverID')  || null;
        const name      = this.getAttribute('name')      || null;
        const status    = this.getAttribute('status')    || null;
        const cpuUsed   = parseFloat(this.getAttribute('cpuUsed'))   || 0.0;
        const ramUsed   = parseFloat(this.getAttribute('ramUsed'))   || 0.0;
        const ramLimit  = parseFloat(this.getAttribute('ramLimit'))  || 0.0;
        const diskUsed  = parseFloat(this.getAttribute('diskUsed'))  || 0.0;
        const diskLimit = parseFloat(this.getAttribute('diskLimit')) || 0.0;

        const isOnline = status === 'running' || status === 'starting';

        // Pourcentages pour les barres
        const ramPct  = ramLimit  > 0 ? Math.min((ramUsed  / ramLimit)  * 100, 100) : 0;
        const diskPct = diskLimit > 0 ? Math.min((diskUsed / diskLimit) * 100, 100) : 0;
        const cpuPct  = Math.min(cpuUsed, 100);

        // Label status traduit
        const statusLabels = {
            running:  'En ligne',
            offline:  'Hors ligne',
            starting: 'Démarrage',
            stopping: 'Arrêt…',
        };
        const statusLabel = statusLabels[status] || 'Inconnu';

        // Formatage Mo → Go si besoin
        const fmt = (mo) => mo >= 1024 ? `${(mo / 1024).toFixed(1)} Go` : `${mo} Mo`;

        this.innerHTML = `
            <div class="minecraft-server-card">

                <div class="server-main-infos">
                    <div class="name">${name}</div>
                    <div class="server-id">${serverID}</div>
                    <div class="status-badge ${status || 'offline'}">
                        <span class="status-dot"></span>
                        ${statusLabel}
                    </div>
                </div>

                <div class="server-infos">

                    <div class="resource-row">
                        <div class="resource-label">
                            <span>CPU</span>
                            <span>${isOnline ? cpuUsed.toFixed(1) + '%' : '—'}</span>
                        </div>
                        <div class="progress-track">
                            <div class="progress-fill ${cpuPct > 80 ? 'alert' : cpuPct > 60 ? 'warn' : ''}"
                                 style="width: ${isOnline ? cpuPct : 0}%"></div>
                        </div>
                    </div>

                    <div class="resource-row">
                        <div class="resource-label">
                            <span>RAM</span>
                            <span>${isOnline ? `${fmt(ramUsed)} / ${fmt(ramLimit)}` : '—'}</span>
                        </div>
                        <div class="progress-track">
                            <div class="progress-fill ${ramPct > 80 ? 'alert' : ramPct > 60 ? 'warn' : ''}"
                                 style="width: ${isOnline ? ramPct : 0}%"></div>
                        </div>
                    </div>

                    <div class="resource-row">
                        <div class="resource-label">
                            <span>DISQUE</span>
                            <span>${isOnline ? `${fmt(diskUsed)} / ${fmt(diskLimit)}` : '—'}</span>
                        </div>
                        <div class="progress-track">
                            <div class="progress-fill ${diskPct > 80 ? 'alert' : diskPct > 60 ? 'warn' : ''}"
                                 style="width: ${isOnline ? diskPct : 0}%"></div>
                        </div>
                    </div>

                </div>

                <div class="buttons">
                    ${status === 'running'
                        ? `<button class="stop-button"    data-id="${serverID}">■ Stop</button>`
                        : `<button class="start-button"   data-id="${serverID}">▶ Démarrer</button>`
                    }
                    <button class="details-button" data-id="${serverID}">Détails</button>
                </div>

            </div>
        `;

        // ── Bouton Start ──
        const startBtn = this.querySelector('.start-button');
        if (startBtn) {
            startBtn.addEventListener('click', async () => {
                startBtn.disabled = true;
                startBtn.textContent = '…';
                try {
                    const r = await fetch('/minecraft/api/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: serverID }),
                    });
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                } catch (e) {
                    console.error('Start error:', e);
                    startBtn.disabled = false;
                    startBtn.textContent = '▶ Démarrer';
                }
            });
        }

        // ── Bouton Stop ──
        const stopBtn = this.querySelector('.stop-button');
        if (stopBtn) {
            stopBtn.addEventListener('click', async () => {
                stopBtn.disabled = true;
                stopBtn.textContent = '…';
                try {
                    const r = await fetch('/minecraft/api/stop', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: serverID }),
                    });
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                } catch (e) {
                    console.error('Stop error:', e);
                    stopBtn.disabled = false;
                    stopBtn.textContent = '■ Stop';
                }
            });
        }

        // ── Bouton Détails ──
        const detailsBtn = this.querySelector('.details-button');
        if (detailsBtn) {
            detailsBtn.addEventListener('click', () => {
                window.location.href = `/minecraft/${serverID}`;
            });
        }
    }
}

customElements.define('minecraft-server-card', MinecraftServerCard);