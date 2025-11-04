import os
import json, time, threading, requests 
from datetime import datetime

CONFIG_PATH = "data/batch_config.json"

def load_configs():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except:
        return []

def run_scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")
        print(now)
        configs = load_configs()
        for id in configs:
            if id["active"] and id["time"] == now:
                try:
                    log_batch_event(f"Execution {id['id']} → {id['endpoint']} con {id['params']}")
                    res = requests.get("http://localhost:8000" + id["endpoint"], params=id["params"])
                    save_batch_response(id["id"], res.text)
                    print(f"[{id['id']}] {id['endpoint']} → {res.status_code}")
                except Exception as e:
                    print(f"[{id['id']}] Errore: {e}")
        time.sleep(60)

def save_batch_response(id_id, response_text):
    path = "data/batch_response.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    responses = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            responses = json.load(f)
    responses[id_id] = {
        "timestamp": datetime.now().isoformat(),
        "response": response_text
    }
    with open(path, "w") as f:
        json.dump(responses, f, indent=2)


def start_scheduler():
    print("start schedule")
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()

def log_batch_event(message):
    path = "data/batch_log.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    logs = []
    if os.path.exists(path):
        with open(path, "r") as f:
            logs = json.load(f)
    logs.insert(0, {"timestamp": datetime.now().isoformat(), "message": message})
    with open(path, "w") as f:
        json.dump(logs[:100], f, indent=2)  # tieni solo gli ultimi 100 log