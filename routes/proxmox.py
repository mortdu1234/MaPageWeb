"""
proxmox_routes.py
=================
Routes Flask pour le dashboard Proxmox.

Dépendances :
    pip install psutil

Facultatif (pour les conteneurs/VMs via l'API Proxmox) :
    pip install proxmoxer requests

Usage dans votre app Flask principale :
    from proxmox_routes import proxmox_bp
    app.register_blueprint(proxmox_bp)
"""

import platform
import socket
import sys
import time
from datetime import datetime

import psutil
from flask import Blueprint, jsonify, render_template

# ── Blueprint ──────────────────────────────────────────────────────────────
proxmox_bp = Blueprint("proxmox", __name__)

# ── Cache réseau (pour calculer les débits) ────────────────────────────────
_net_cache = {"timestamp": 0, "counters": {}}


def _get_net_rates():
    """Calcule le débit réseau (octets/s) depuis le dernier appel."""
    now = time.time()
    current = psutil.net_io_counters(pernic=True)

    elapsed = now - _net_cache["timestamp"]
    prev = _net_cache["counters"]

    rates = {}
    for iface, stats in current.items():
        if iface in prev and elapsed > 0:
            rates[iface] = {
                "bytes_sent":      stats.bytes_sent,
                "bytes_recv":      stats.bytes_recv,
                "bytes_sent_rate": (stats.bytes_sent - prev[iface].bytes_sent) / elapsed,
                "bytes_recv_rate": (stats.bytes_recv - prev[iface].bytes_recv) / elapsed,
            }
        else:
            rates[iface] = {
                "bytes_sent":      stats.bytes_sent,
                "bytes_recv":      stats.bytes_recv,
                "bytes_sent_rate": 0,
                "bytes_recv_rate": 0,
            }

    _net_cache["timestamp"] = now
    _net_cache["counters"] = current
    return rates


def _get_temperatures():
    """Retourne les températures disponibles (Linux seulement)."""
    temps = {}
    if not hasattr(psutil, "sensors_temperatures"):
        return temps

    sensors = psutil.sensors_temperatures()
    for chip, entries in sensors.items():
        for entry in entries:
            label = entry.label or chip
            key = f"{chip} — {label}" if entry.label else chip
            # Garder uniquement la valeur la plus élevée par clé
            if key not in temps or entry.current > temps[key]["current"]:
                temps[key] = {
                    "current":  round(entry.current, 1),
                    "high":     round(entry.high, 1) if entry.high else None,
                    "critical": round(entry.critical, 1) if entry.critical else None,
                }
    return temps


def _get_disks():
    """Retourne les partitions montées avec leur utilisation."""
    disks = []
    for part in psutil.disk_partitions(all=False):
        # Ignorer les systèmes de fichiers virtuels
        if part.fstype in ("tmpfs", "devtmpfs", "squashfs", "overlay", ""):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        disks.append({
            "device":     part.device,
            "mountpoint": part.mountpoint,
            "fstype":     part.fstype,
            "total":      usage.total,
            "used":       usage.used,
            "free":       usage.free,
            "percent":    round(usage.percent, 1),
        })
    return disks


def _get_vms():
    """
    Retourne la liste des conteneurs LXC et VMs via l'API Proxmox.
    Nécessite proxmoxer + les variables d'environnement ou la config ci-dessous.
    Si proxmoxer n'est pas installé, retourne une liste vide.
    """
    try:
        from proxmoxer import ProxmoxAPI  # type: ignore
        import os

        host  = os.environ.get("PROXMOX_HOST", "localhost")
        user  = os.environ.get("PROXMOX_USER", "root@pam")
        token = os.environ.get("PROXMOX_TOKEN_NAME", "")
        value = os.environ.get("PROXMOX_TOKEN_VALUE", "")
        node  = os.environ.get("PROXMOX_NODE", "pve")
        verify = os.environ.get("PROXMOX_VERIFY_SSL", "false").lower() == "true"

        if token and value:
            prox = ProxmoxAPI(host, user=user, token_name=token,
                              token_value=value, verify_ssl=verify)
        else:
            password = os.environ.get("PROXMOX_PASSWORD", "")
            prox = ProxmoxAPI(host, user=user, password=password,
                              verify_ssl=verify)

        vms = []
        for item in prox.nodes(node).lxc.get():
            vms.append({
                "vmid":   item["vmid"],
                "name":   item.get("name", f"CT {item['vmid']}"),
                "status": item.get("status", "unknown"),
                "type":   "LXC",
            })
        for item in prox.nodes(node).qemu.get():
            vms.append({
                "vmid":   item["vmid"],
                "name":   item.get("name", f"VM {item['vmid']}"),
                "status": item.get("status", "unknown"),
                "type":   "QEMU",
            })
        return sorted(vms, key=lambda x: (x["status"] != "running", x["name"]))

    except Exception:
        return []


def _get_cpu_model():
    """Lit le modèle CPU depuis /proc/cpuinfo (Linux)."""
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "—"


def _get_ip():
    """Retourne l'IP LAN de la machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "—"


# ── Routes ────────────────────────────────────────────────────────────────

@proxmox_bp.route("/proxmox")
def proxmox_page():
    """Page HTML du dashboard."""
    return render_template("proxmox.html")


@proxmox_bp.route("/api/proxmox/stats")
def proxmox_stats():
    """Endpoint JSON consommé par proxmox.js."""

    # CPU
    cpu_pct = psutil.cpu_percent(interval=0.5)
    cpu_freq = psutil.cpu_freq()

    # Mémoire
    mem  = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Uptime
    boot_ts = psutil.boot_time()
    uptime_s = int(time.time() - boot_ts)
    boot_dt = datetime.fromtimestamp(boot_ts).strftime("%d/%m/%Y %H:%M")

    # Load average (Linux)
    try:
        load_avg = list(psutil.getloadavg())
    except AttributeError:
        load_avg = None

    data = {
        "cpu": {
            "percent":       round(cpu_pct, 1),
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores":  psutil.cpu_count(logical=True),
            "model":          _get_cpu_model(),
            "freq_current":   round(cpu_freq.current, 0) if cpu_freq else None,
            "freq_max":       round(cpu_freq.max, 0)     if cpu_freq else None,
        },
        "memory": {
            "total":   mem.total,
            "used":    mem.used,
            "free":    mem.available,
            "percent": round(mem.percent, 1),
        },
        "swap": {
            "total":   swap.total,
            "used":    swap.used,
            "free":    swap.free,
            "percent": round(swap.percent, 1),
        },
        "uptime": {
            "seconds":   uptime_s,
            "boot_time": boot_dt,
        },
        "temperatures": _get_temperatures(),
        "disks":        _get_disks(),
        "network":      _get_net_rates(),
        "vms":          _get_vms(),
        "system": {
            "hostname":       socket.gethostname(),
            "os":             f"{platform.system()} {platform.release()}",
            "kernel":         platform.release(),
            "arch":           platform.machine(),
            "python_version": sys.version.split()[0],
            "ip_address":     _get_ip(),
            "cpu_model":      _get_cpu_model(),
            "pid_count":      len(psutil.pids()),
            "load_avg":       load_avg,
        },
    }

    return jsonify(data)