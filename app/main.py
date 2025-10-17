from datetime import datetime
import time
import json
from flask import Flask, request, jsonify
from core import login_and_cache_state, rerun_pipeline, runtime_pipeline, log_pipeline, fullExtract_pipeline, extract_userStatus, status_pipeline, getID_pipeline, setFileMapping
from legacy.WebService.ConfigParser import parse_config
from filelock import FileLock

# Config: Log-In Refresh Parameters
LOCK_FILE = "state.lock"
REFRESH_INTERVAL = 3600  #1 hour
last_login_time = 0

#Login function not exposed. Login managed via config.ini file
def api_login():
    organisation_id, mail, password = parse_config("legacy/WebService/config.ini")
    login_and_cache_state(organisation_id, mail, password)

def load_state():   #Reading the sharedState.json file and returning its content
    try:
        with open("sharedState.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_login_time": 0}

def save_state(state):  #Updating the sharedState.json file with the state input
    with open("sharedState.json", "w") as f:
        json.dump(state, f)

def ensure_valid_login():   #Handle Login Check and Refresh
    state = load_state()
    if time.time() - state["last_login_time"] > REFRESH_INTERVAL:  #Checking if last login after refresh_interval
        lock = FileLock(LOCK_FILE)
        print("Accessing state.lock...")
        with lock.acquire():
            # Re-Checking timings inside lock to avoid race condition
            state = load_state()
            if time.time() - state["last_login_time"] > REFRESH_INTERVAL:
                print("Login Refresh...")
                api_login()
                state["last_login_time"] = int(time.time())
                save_state(state)
            else:
                print("Login already updated")

def setFileMapping(bifrost_instance: str):    #Update the pipeline mapping file if empty or older than 24 hours
    if bifrost_instance == "":
        with open(f"client/bifrost_instance.json", "r", encoding="utf-8") as f:
                instance = json.load(f)
        for bifrost_instance in instance["bifrost_instances"]:
            with open(f"client/{bifrost_instance}/pipeline.json", "r", encoding="utf-8") as f:
                    pipelines = json.load(f)
            if len(pipelines["pipelines"]) == 0 and (datetime.now() - pipelines["last_updated"]) < datetime.timedelta(hours=24):
                setFileMapping(bifrost_instance)
    else:
        with open(f"client/{bifrost_instance}/pipeline.json", "r", encoding="utf-8") as f:
                pipelines = json.load(f)
        if len(pipelines["pipelines"]) == 0 and (datetime.now() - pipelines["last_updated"]) < datetime.timedelta(hours=24):
            setFileMapping(bifrost_instance)


def create_app():
    app = Flask(__name__)

    @app.before_request
    def check_login_before_request():   #Before every API request, check if login state is updated
        print("Checking login state before request..." )#+ datetime.datetime.now().isoformat())
        ensure_valid_login()
        setFileMapping(request.args.get("bifrost_instance", ""))

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    #Call to function: pipeline_rerun
    @app.post("/api/rerun")
    def pipeline_rerun():
        print("pipeline_rerun: Starting")
        pipeline_name = request.args.get("pipeline_name")
        bifrost_instance = request.args.get("bifrost_instance")
        if not pipeline_name or not bifrost_instance:
            return jsonify({"error": "pipeline_id and bifrost_instance required"}), 400
        try:
            res = rerun_pipeline(pipeline_name, bifrost_instance)
            print("pipeline_rerun: Completed")
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    #Call to function: pipeline_runtime
    @app.get("/api/runtime")
    def pipeline_runtime():
        print("pipeline_runtime: Starting")
        pipeline_name = request.args.get("pipeline_name")
        bifrost_instance = request.args.get("bifrost_instance")
        if not pipeline_name or not bifrost_instance:
            return jsonify({"error": "pipeline_name and bifrost_instance required"}), 400
        try:
            res = runtime_pipeline(pipeline_name, bifrost_instance)
            print("pipeline_runtime: Completed")
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    #Call to function: pipeline_runtime
    @app.get("/api/getID")
    def pipeline_getID():
        print("pipeline_runtime: Starting")
        bifrost_instance = request.args.get("bifrost_instance")
        if not bifrost_instance:
            return jsonify({"error": "bifrost_instance required"}), 400
        try:
            res = getID_pipeline(bifrost_instance)
            print("pipeline_runtime: Completed")
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    #Call to function: pipeline_status
    @app.get("/api/pipelineStatus")
    def pipeline_status():
        print("pipeline_Status: Starting")
        bifrost_instance = request.args.get("bifrost_instance")
        status_filter = request.args.get("status_filter")
        if not status_filter or not bifrost_instance:
            return jsonify({"error": "status_filter and bifrost_instance required"}), 400
        try:
            res = status_pipeline(status_filter, bifrost_instance)
            print("pipeline_Status: Completed")
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Call to function: pipeline_log
    @app.get("/api/lastLog")
    def pipeline_log():
        print("pipeline_log: Starting")
        pipeline_name = request.args.get("pipeline_name")
        bifrost_instance = request.args.get("bifrost_instance")
        if not pipeline_name or not bifrost_instance:
            return jsonify({"error": "pipeline_name and bifrost_instance required"}), 400
        try:
            res = log_pipeline(pipeline_name, bifrost_instance)
            print("pipeline_log: Completed")
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Call to function: pipeline_fullExtract
    #TODO handle long task timeout, thread handling
    @app.get("/api/pipelineFullExtract")
    def pipeline_fullExtract():
        print("pipeline_fullExtract: Starting")
        bifrost_instance = request.args.get("bifrost_instance")
        status_filter = request.args.get("status_filter")
        if not status_filter or not bifrost_instance:
            return jsonify({"error": "status_filter and bifrost_instance required"}), 400
        try:
            res = fullExtract_pipeline(status_filter, bifrost_instance)
            print("pipeline_fullExtract: Completed")
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Call to function: userStatus_extract
    @app.get("/api/userStatus")
    def userStatus_extract():
        print("userStatus_extract: Starting")
        visualfabriq_instance = request.args.get("visualfabriq_instance")

        if not visualfabriq_instance:
            visualfabriq_instance = ""  #NON E PIU NECESSARIO PASSARE VISUALFABRIQ_INSTANCE COME PARAMETRO
            #return jsonify({"error": "visualfabriq_instance required"}), 400
        try:
            res, vf_instance = extract_userStatus(visualfabriq_instance)
            res["visualfabriq_instance"] = vf_instance    #Adding the visualfabriq_instance to the output
            print("userStatus_extract: Completed")
            return jsonify(res)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


# Instance for gunicorn "app.main:app"
app = create_app()
ensure_valid_login() #Manage login after creating the app
print("Login completed, calls can be made now")

