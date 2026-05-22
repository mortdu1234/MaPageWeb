"""
proxmox_routes.py — Backend Flask pour dashboard Proxmox
=========================================================
Toutes les métriques viennent de l'API REST Proxmox (:8006).

Variables d'environnement requises :
    PROXMOX_HOST         IP ou hostname du nœud (ex: 192.168.1.10)
    PROXMOX_NODE         Nom du nœud (ex: pve)
    PROXMOX_USER         ex: root@pam
    PROXMOX_TOKEN_NAME   ex: flask-dashboard
    PROXMOX_TOKEN_VALUE  Le secret du token

Optionnel :
    PROXMOX_VERIFY_SSL   true | false (défaut: false)
    PROXMOX_PORT         défaut: 8006

pip install requests
"""

import os
import time
import requests
import urllib3
from flask import Blueprint, jsonify, render_template

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxmox_bp = Blueprint("proxmox", __name__)

# ── Config ────────────────────────────────────────────────────────────────

def _cfg():
    return {
        "host":       os.environ.get("PROXMOX_HOST", "192.168.1.1"),
        "port":       int(os.environ.get("PROXMOX_PORT", "8006")),
        "node":       os.environ.get("PROXMOX_NODE", "pve"),
        "user":       os.environ.get("PROXMOX_USER", "root@pam"),
        "token_name": os.environ.get("PROXMOX_TOKEN_NAME", "flask-dashboard"),
        "token_val":  os.environ.get("PROXMOX_TOKEN_VALUE", ""),
        "verify_ssl": os.environ.get("PROXMOX_VERIFY_SSL", "false").lower() == "true",
    }

def _session(cfg):
    s = requests.Session()
    s.verify = cfg["verify_ssl"]
    s.headers.update({
        "Authorization": f"PVEAPIToken={cfg['user']}!{cfg['token_name']}={cfg['token_val']}"
    })
    return s

def _base(cfg):
    return f"https://{cfg['host']}:{cfg['port']}/api2/json"

def _get(path, cfg=None):
    if cfg is None:
        cfg = _cfg()
    s = _session(cfg)
    r = s.get(_base(cfg) + path, timeout=5)
    r.raise_for_status()
    return r.json().get("data", {})

# ── Helpers ───────────────────────────────────────────────────────────────

def _fmt_bytes(b):
    if b is None:
        return "—"
    for unit in ("o", "Ko", "Mo", "Go", "To"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} Po"

def _uptime_str(seconds):
    if not seconds:
        return "—"
    d = int(seconds // 86400)
    h = int((seconds % 86400) // 3600)
    m = int((seconds % 3600) // 60)
    parts = []
    if d: parts.append(f"{d}j")
    if h: parts.append(f"{h}h")
    parts.append(f"{m}min")
    return " ".join(parts)

# ── Collecte données ──────────────────────────────────────────────────────

def _node_status(cfg, node):
    """Métriques principales du nœud."""
    d = _get(f"/nodes/{node}/status", cfg)

    cpu_pct   = round(d.get("cpu", 0) * 100, 1)
    mem       = d.get("memory", {})
    swap      = d.get("swap", {})
    root_fs   = d.get("rootfs", {})
    uptime_s  = d.get("uptime", 0)
    load_avg  = d.get("loadavg", [])
    cpu_info  = d.get("cpuinfo", {})
    ksm       = d.get("ksm", {})

    return {
        "cpu": {
            "percent":        cpu_pct,
            "physical_cores": cpu_info.get("cpus", "—"),
            "sockets":        cpu_info.get("sockets", "—"),
            "model":          cpu_info.get("model", "—"),
            "mhz":            cpu_info.get("mhz", "—"),
        },
        "memory": {
            "total":   mem.get("total", 0),
            "used":    mem.get("used", 0),
            "free":    mem.get("free", 0),
            "percent": round(mem.get("used", 0) / mem.get("total", 1) * 100, 1) if mem.get("total") else 0,
        },
        "swap": {
            "total":   swap.get("total", 0),
            "used":    swap.get("used", 0),
            "free":    swap.get("free", 0),
            "percent": round(swap.get("used", 0) / swap.get("total", 1) * 100, 1) if swap.get("total") else 0,
        },
        "rootfs": {
            "total":   root_fs.get("total", 0),
            "used":    root_fs.get("used", 0),
            "free":    root_fs.get("free", 0),
            "avail":   root_fs.get("avail", 0),
            "percent": round(root_fs.get("used", 0) / root_fs.get("total", 1) * 100, 1) if root_fs.get("total") else 0,
        },
        "uptime": {
            "seconds": uptime_s,
            "human":   _uptime_str(uptime_s),
        },
        "load_avg": load_avg,
        "ksm_shared": ksm.get("shared", 0),
    }

def _node_storage(cfg, node):
    """Tous les stockages Proxmox du nœud."""
    items = _get(f"/nodes/{node}/storage", cfg)
    result = []
    for s in (items if isinstance(items, list) else []):
        if s.get("active") != 1:
            continue
        total = s.get("total", 0)
        used  = s.get("used", 0)
        avail = s.get("avail", 0)
        pct   = round(used / total * 100, 1) if total else 0
        result.append({
            "storage":  s.get("storage", "—"),
            "type":     s.get("type", "—"),
            "content":  s.get("content", ""),
            "total":    total,
            "used":     used,
            "avail":    avail,
            "percent":  pct,
            "shared":   s.get("shared", 0),
        })
    return result

def _node_temps(cfg, node):
    """Températures via endpoint Proxmox (disponible sur les hôtes bare-metal)."""
    try:
        data = _get(f"/nodes/{node}/hardware/pci", cfg)
        # Les températures passent par /nodes/{node}/status -> thermalstate (PVE 8+)
        # ou via les sensors rpcapi
    except Exception:
        pass

    # Proxmox expose les températures dans node/status sous "thermalstate" (PVE 8+)
    # Sinon, on essaie le endpoint direct
    temps = {}
    try:
        raw = _get(f"/nodes/{node}/status", cfg)
        thermal = raw.get("thermalstate", "")
        # Format: "temp=45.0°C"  (string brut lm-sensors)
        if thermal:
            temps["Système"] = {
                "current":  float(thermal.replace("temp=","").replace("°C","").strip()),
                "high":     85,
                "critical": 95,
            }
    except Exception:
        pass

    # Endpoint dédié capteurs (PVE 7.4+ avec lm-sensors installé)
    try:
        sensors = _get(f"/nodes/{node}/hardware/sensors", cfg)
        if isinstance(sensors, list):
            for chip in sensors:
                name = chip.get("chip", "capteur")
                for key, val in chip.items():
                    if key.endswith("_input"):
                        label = key.replace("_input", "")
                        try:
                            t = float(val)
                            if 0 < t < 150:
                                high = chip.get(f"{label}_max")
                                crit = chip.get(f"{label}_crit")
                                temps[f"{name} — {label}"] = {
                                    "current":  round(t, 1),
                                    "high":     float(high) if high else 85,
                                    "critical": float(crit) if crit else 95,
                                }
                        except (ValueError, TypeError):
                            pass
    except Exception:
        pass

    return temps

def _node_disks(cfg, node):
    """Liste des disques physiques du nœud."""
    try:
        disks = _get(f"/nodes/{node}/disks/list", cfg)
        result = []
        for d in (disks if isinstance(disks, list) else []):
            result.append({
                "devpath": d.get("devpath", "—"),
                "model":   d.get("model", "—"),
                "size":    d.get("size", 0),
                "type":    d.get("type", "—"),      # ssd, hdd, nvme
                "health":  d.get("health", "—"),
                "rpm":     d.get("rpm", None),
                "wearout": d.get("wearout", None),  # SSD wear level
                "serial":  d.get("serial", "—"),
            })
        return result
    except Exception:
        return []

def _node_network(cfg, node):
    """Interfaces réseau configurées sur le nœud."""
    try:
        ifaces = _get(f"/nodes/{node}/network", cfg)
        result = []
        for iface in (ifaces if isinstance(ifaces, list) else []):
            if iface.get("type") in ("bridge", "eth", "bond", "vlan"):
                result.append({
                    "iface":    iface.get("iface", "—"),
                    "type":     iface.get("type", "—"),
                    "address":  iface.get("address", "—"),
                    "netmask":  iface.get("netmask", "—"),
                    "active":   iface.get("active", 0),
                    "autostart":iface.get("autostart", 0),
                    "bridge_ports": iface.get("bridge_ports", ""),
                })
        return result
    except Exception:
        return []

def _node_vms(cfg, node):
    """Conteneurs LXC et VMs QEMU avec métriques."""
    result = []

    try:
        lxcs = _get(f"/nodes/{node}/lxc", cfg)
        for c in (lxcs if isinstance(lxcs, list) else []):
            maxmem = c.get("maxmem", 0)
            mem    = c.get("mem", 0)
            result.append({
                "vmid":    c.get("vmid"),
                "name":    c.get("name", f"CT {c.get('vmid')}"),
                "type":    "LXC",
                "status":  c.get("status", "unknown"),
                "cpu":     round(c.get("cpu", 0) * 100, 1),
                "mem":     mem,
                "maxmem":  maxmem,
                "mem_pct": round(mem / maxmem * 100, 1) if maxmem else 0,
                "disk":    c.get("disk", 0),
                "maxdisk": c.get("maxdisk", 0),
                "uptime":  _uptime_str(c.get("uptime", 0)),
                "netin":   c.get("netin", 0),
                "netout":  c.get("netout", 0),
            })
    except Exception:
        pass

    try:
        vms = _get(f"/nodes/{node}/qemu", cfg)
        for v in (vms if isinstance(vms, list) else []):
            maxmem = v.get("maxmem", 0)
            mem    = v.get("mem", 0)
            result.append({
                "vmid":    v.get("vmid"),
                "name":    v.get("name", f"VM {v.get('vmid')}"),
                "type":    "QEMU",
                "status":  v.get("status", "unknown"),
                "cpu":     round(v.get("cpu", 0) * 100, 1),
                "mem":     mem,
                "maxmem":  maxmem,
                "mem_pct": round(mem / maxmem * 100, 1) if maxmem else 0,
                "disk":    v.get("disk", 0),
                "maxdisk": v.get("maxdisk", 0),
                "uptime":  _uptime_str(v.get("uptime", 0)),
                "netin":   v.get("netin", 0),
                "netout":  v.get("netout", 0),
            })
    except Exception:
        pass

    return sorted(result, key=lambda x: (x["status"] != "running", x["name"].lower()))

def _node_sysinfo(cfg, node):
    """Informations système du nœud (version PVE, kernel, etc.)."""
    try:
        ver  = _get(f"/nodes/{node}/version", cfg)
        stat = _get(f"/nodes/{node}/status", cfg)
        return {
            "hostname":    stat.get("name", node),
            "pve_version": ver.get("version", "—"),
            "pve_release": ver.get("release", "—"),
            "kernel":      stat.get("kversion", "—"),
            "cpu_model":   stat.get("cpuinfo", {}).get("model", "—"),
            "cpu_sockets": stat.get("cpuinfo", {}).get("sockets", "—"),
            "cpu_cores":   stat.get("cpuinfo", {}).get("cpus", "—"),
            "arch":        "x86_64",
        }
    except Exception:
        return {}

# ── Routes ────────────────────────────────────────────────────────────────

@proxmox_bp.route("/proxmox")
def proxmox_page():
    return render_template("proxmox.html")

@proxmox_bp.route("/api/proxmox/stats")
def proxmox_stats():
    try:
        cfg  = _cfg()
        node = cfg["node"]

        status  = _node_status(cfg, node)
        storage = _node_storage(cfg, node)
        temps   = _node_temps(cfg, node)
        disks   = _node_disks(cfg, node)
        network = _node_network(cfg, node)
        vms     = _node_vms(cfg, node)
        sysinfo = _node_sysinfo(cfg, node)

        return jsonify({
            "cpu":          status["cpu"],
            "memory":       status["memory"],
            "swap":         status["swap"],
            "uptime":       status["uptime"],
            "load_avg":     status["load_avg"],
            "temperatures": temps,
            "storage":      storage,
            "disks":        disks,
            "network":      network,
            "vms":          vms,
            "system":       sysinfo,
        })

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Impossible de joindre Proxmox. Vérifiez PROXMOX_HOST et le réseau."}), 503
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"Erreur API Proxmox : {e.response.status_code}"}), e.response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500