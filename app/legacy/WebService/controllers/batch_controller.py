# batch_controller.py
import json, os
import re
from flask import Blueprint, render_template, request, jsonify
from controllers.scheduler import log_batch_event, save_batch_response
import requests

batch_bp = Blueprint("batch", __name__, template_folder="templates")
CONFIG_PATH = "data/batch_config.json"
os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)


def load_configs():
    if not os.path.exists(CONFIG_PATH):
        return []
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_configs(configs):
    with open(CONFIG_PATH, "w") as f:
        json.dump(configs, f, indent=2)
    print("Saving configs to:", CONFIG_PATH)


@batch_bp.route("/batch")
def batch_page():
    return render_template("batch.html")

@batch_bp.route("/batch/configs")
def get_configs():
    return jsonify(load_configs())

def next_id_id(configs):
    # Estrai tutti gli ID numerici tipo "id_005"
    ids = [int(re.search(r"id_(\d+)", id["id"]).group(1)) for id in configs]
    max_id = max(ids) if ids else 0
    return f"id_{max_id + 1:05d}"

@batch_bp.route("/batch/save", methods=["POST"])
def save_config():
    data = request.json
    configs = load_configs()
    data["id"] = next_id_id(configs)
    configs.append(data)
    save_configs(configs)
    return jsonify({"status": "saved", "id": data["id"]})

@batch_bp.route("/batch/toggle", methods=["POST"])
def toggle_config():
    data = request.json
    configs = load_configs()
    for id in configs:
        if id["id"] == data["id"]:
            id["active"] = data["active"]
            break
    save_configs(configs)
    return jsonify({"status": "updated"})

@batch_bp.route("/batch/delete", methods=["POST"])
def delete_config():
    data = request.json
    configs = load_configs()
    configs = [id for id in configs if id["id"] != data["id"]]
    save_configs(configs)
    return jsonify({"status": "deleted"})

@batch_bp.route("/batch/logs")
def get_logs():
    path = "data/batch_log.json"
    if not os.path.exists(path):
        return jsonify([])
    with open(path, "r") as f:
        return jsonify(json.load(f))

@batch_bp.route("/batch/responses")
def get_batch_responses():
    path = "data/batch_response.json"
    if not os.path.exists(path):
        return jsonify([])
    with open(path, "r") as f:
        return jsonify(json.load(f))

@batch_bp.route("/batch/run", methods=["POST"])
def run_batch():
    data = request.json
    endpoint = data.get("endpoint")
    params = data.get("params", {})
    print(endpoint)
    print(data)
    print(params)
    try:
        log_batch_event(f"Execution {id['id']} → {id['endpoint']} con {id['params']}")
        res = requests.get("http://localhost:8000" + id["endpoint"], params=id["params"])
        save_batch_response(id["id"], res.text)
        print(f"[{id['id']}] {id['endpoint']} → {res.status_code}")

        return jsonify({"status": "ok", "response": res.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


