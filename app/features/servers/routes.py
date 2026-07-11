"""Routes de serveurs du package app."""

from flask import Blueprint, jsonify, render_template

from app.features.servers.proxmox_client import *
from routes import require_permission
from routes.serverHub import serverhub_bp

proxmox_bp = Blueprint(
    "proxmox",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/proxmox/static",
)


@proxmox_bp.route("/proxmox")
@require_permission("admin")
def proxmox_page():
    return render_template("proxmox.html")


@proxmox_bp.route("/api/proxmox/stats")
@require_permission("admin")
def proxmox_stats():
    try:
        cfg = _cfg()
        node = cfg["node"]
        status = _node_status(cfg, node)
        storage = _node_storage(cfg, node)
        temps = _node_temps(cfg, node)
        disks = _node_disks(cfg, node)
        network = _node_network(cfg, node)
        vms = _node_vms(cfg, node)
        sysinfo = _node_sysinfo(cfg, node)

        return jsonify({
            "cpu": status["cpu"],
            "memory": status["memory"],
            "swap": status["swap"],
            "uptime": status["uptime"],
            "load_avg": status["load_avg"],
            "temperatures": temps,
            "storage": storage,
            "disks": disks,
            "network": network,
            "vms": vms,
            "system": sysinfo,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


__all__ = ["proxmox_bp", "serverhub_bp"]
