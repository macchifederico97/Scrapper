from datetime import datetime, timedelta
import os
import time
import json
from flask import Flask, render_template, request, jsonify
from core import login_and_cache_state, rerun_pipeline, runtime_pipeline, log_pipeline, fullExtract_pipeline, extract_userStatus, status_pipeline, getID_pipeline, increaseTimeout_pipeline, increaseJobSize_pipeline, complete_rerun_pipeline
from legacy.WebService.ConfigParser import parse_config
from filelock import FileLock
#from legacy.WebService.controllers.scheduler import start_scheduler
#start_scheduler()

#from legacy.WebService.controllers.batch_controller import batch_bp

template_path = os.path.join(os.path.dirname(__file__), "legacy/WebService/templates")
app = Flask(__name__, template_folder=template_path)
#app.register_blueprint(batch_bp)

@app.route("/")
def home():
    try:
        return render_template("home.html")
    except Exception as e:
        return f"Errore nel rendering: {e}", 500


# Config: Log-In Refresh Parameters
LOCK_FILE_LOGIN = "login.lock"
LOCK_FILE_PIPELINE_ID = "pipeline_id.lock"
REFRESH_INTERVAL = 3600  #1 hour    #TODO TOCHANGE
REFRESH_INTERNAL_PIPELINE_ID = 60 #1 hour #TODO TOCHANGE
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
        lock = FileLock(LOCK_FILE_LOGIN)
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

def ensure_valid_pipeline_id(bifrost_instance,  call_from : str, minutes_delta : int,  filterEnabled: bool = False):    #Update the pipeline mapping file if empty or older than 24 hours
    lock = FileLock(LOCK_FILE_PIPELINE_ID)
    if bifrost_instance == "" or bifrost_instance is None:
        with open(f"client/bifrost_instance.json", "r", encoding="utf-8") as f:
                instance = json.load(f)
        for bifrost_instance_json in instance:
            name_instance = bifrost_instance_json.get("bifrost_instance")
            with open(f"client/{name_instance}/pipeline.json", "r", encoding="utf-8") as f:
                pipelines = json.load(f)
            if call_from == "create_app" and datetime.strptime(pipelines["last_updated"], "%Y-%m-%dT%H:%M:%S").date() < datetime.now().date():
                with lock.acquire(): #FILE LOCK
                    getID_pipeline(name_instance, filterEnabled) 
            else:
                if len(pipelines["pipelines"]) == 0 or (datetime.now() - datetime.strptime(pipelines["last_updated"], "%Y-%m-%dT%H:%M:%S")) > timedelta(minutes = minutes_delta):  #CONTROLLO SE AGGIORNARE IL FILE CON LE PIPELINE ID
                    with lock.acquire(): #FILE LOCK
                        getID_pipeline(name_instance, filterEnabled) 
    else:
        with open(f"client/{bifrost_instance}/pipeline.json", "r", encoding="utf-8") as f:
            pipelines = json.load(f)
        if len(pipelines["pipelines"]) == 0 or (datetime.now() - datetime.strptime(pipelines["last_updated"], "%Y-%m-%dT%H:%M:%S")) > timedelta(minutes_delta):
            with lock.acquire():    #FILE LOCK
                getID_pipeline(bifrost_instance, filterEnabled)


#def create_app():
#    app = Flask(__name__)

@app.before_request
def check_login_before_request():   #Before every API request, check if login state is updated
    print("Checking login state and pipeline_id before request..." )
    ensure_valid_login()
    bifrost_instance = request.args.get("bifrost_instance")
    if bifrost_instance:
        ensure_valid_pipeline_id(bifrost_instance, "before_request", REFRESH_INTERNAL_PIPELINE_ID, True)
    else:
        ensure_valid_pipeline_id(None, "before_request", REFRESH_INTERNAL_PIPELINE_ID, True)
    print("Login State and Pipeline_id are currently updated")

@app.post("/batch/run")
def batch_run():
    print("batch_run: Received request")
    try:
        data = request.get_json()
        job_id = data.get("id")
        endpoint = data.get("endpoint")
        params = data.get("params", {})

        print(f"batch_run: Dispatching {job_id} → {endpoint} with params {params}")

        # Dispatch manual routing
        match endpoint:
            case "/healthz":
                return {"status": "ok"}
            case "/api/rerun":
                return rerun_pipeline_func(params)
            case "/api/moveFileRerun":
                return complete_rerun_pipeline_func(params)
            case "/api/runtime":
                return runtime_pipeline_func(params)
            case "/api/getID":
                return getID_pipeline_func(params)
            case "/api/pipelineStatus":
                return status_pipeline_func(params)
            case "/api/lastLog":
                return log_pipeline_func(params)
            case "/api/pipelineFullExtract":
                return fullExtract_pipeline_func(params)
            #doppio?? #TODO
            case "/api/pipelineUpdateId":
                return getID_pipeline_func(params)
            case "/api/pipelineIncreaseTimeout":
                return increaseTimeout_pipeline_func(params)
            case "/api/pipelineIncreaseJobSize":
                return increaseJobSize_pipeline_func(params)
            case "/api/userStatus":
                return extract_userStatus_func(params)
            case _:
                return jsonify({"error": f"Unknown endpoint: {endpoint}"}), 400
    except Exception as e:
        print(f"batch_run: Error → {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.get("/healthz")
def healthz():
    return {"status": "ok"}



#Call to function: pipeline_rerun
@app.post("/api/rerun")
def pipeline_rerun():
    rerun_pipeline_func(request)
    
# Call to function: pipeline_rerun
@app.post("/api/moveFileRerun")
def pipeline_complete_rerun():
    complete_rerun_pipeline_func(request)

#Call to function: pipeline_runtime
@app.get("/api/runtime")
def pipeline_runtime():
    runtime_pipeline_func(request)

#Call to function: pipeline_getID
@app.get("/api/getID")
def pipeline_getID():
    getID_pipeline_func(request)
    
#Call to function: pipeline_status
@app.get("/api/pipelineStatus")
def pipeline_status():
    status_pipeline_func(request)
    
# Call to function: pipeline_log
@app.get("/api/lastLog")
def pipeline_log():
    log_pipeline_func(request)

# Call to function: pipeline_fullExtract
@app.get("/api/pipelineFullExtract")
def pipeline_fullExtract():
    fullExtract_pipeline_func(request)

# Call to function: pipeline_update_Id, Manual Pipeline Id Update
@app.get("/api/pipelineUpdateId")
def pipeline_update_id():
    print("pipeline_update_id: Starting")
    bifrost_instance = request.args.get("bifrost_instance")
    status_filter = request.args.get("status_filter")
    if not status_filter or not bifrost_instance:
        return jsonify({"error": "status_filter and bifrost_instance required"}), 400
    try:
        if status_filter.lower() == "true":
            statusBool = True
        else: statusBool = False
        res = getID_pipeline(bifrost_instance, statusBool)
        print("pipeline_update_id: Completed")
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Call to function: pipeline_increase_timeout
@app.post("/api/pipelineIncreaseTimeout")
def pipeline_increaseTimeout():
    increaseTimeout_pipeline_func(request)
    
# Call to function: pipeline_increase_job_size
@app.post("/api/pipelineIncreaseJobSize")
def pipeline_increaseJobSize():
    increaseJobSize_pipeline_func(request)

# Call to function: userStatus_extract
@app.get("/api/userStatus")
def userStatus_extract():
    extract_userStatus_func(request)


#FUNCION

#"/api/rerun"
def rerun_pipeline_func(request):
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

#/api/moveFileRerun
def complete_rerun_pipeline_func(request):
    print("pipeline_moveFileRerun: Starting")
    pipeline_name = request.args.get("pipeline_name")
    bifrost_instance = request.args.get("bifrost_instance")
    if not pipeline_name or not bifrost_instance:
        return jsonify({"error": "pipeline_moveFileRerun: pipeline_id and bifrost_instance required"}), 400
    try:
        res = complete_rerun_pipeline(pipeline_name, bifrost_instance)
        print("pipeline_moveFileRerun: Completed")
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": "pipeline_moveFileRerun: "+str(e)}), 500 

#"/api/runtime"   
def runtime_pipeline_func(request):
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

#"/api/getID"
def getID_pipeline_func(request):
    print("pipeline_runtime: Starting")
    bifrost_instance = request.args.get("bifrost_instance")
    filterEnabled = request.args.get("filter")
    if not bifrost_instance:
        return jsonify({"error": "bifrost_instance required"}), 400
    try:
        res = getID_pipeline(bifrost_instance, filterEnabled=True if filterEnabled == "true" else False)
        print("pipeline_runtime: Completed")
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#"/api/pipelineStatus"
def status_pipeline_func(request):
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

#"/api/lastLog"
def log_pipeline_func(request):
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

#"/api/pipelineFullExtract"
def fullExtract_pipeline_func(request):
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

#"/api/pipelineIncreaseTimeout"
def increaseTimeout_pipeline_func(request):
    print("pipeline_increase_timeout: Starting")
    pipeline_name = request.args.get("pipeline_name")
    bifrost_instance = request.args.get("bifrost_instance")
    delta_increase = request.args.get("delta_increase")
    processing_step_nr = request.args.get("processing_step_nr")
    if not pipeline_name or not bifrost_instance or not delta_increase or not processing_step_nr:
        return jsonify({"error": "pipeline_name, bifrost_instance, delta_increase and processing_step_nr required"}), 400
    try:
        res = increaseTimeout_pipeline(pipeline_name, bifrost_instance, int(delta_increase), int(processing_step_nr))
        print("pipeline_increase_timeout: Completed")
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#"/api/pipelineIncreaseJobSize"
def increaseJobSize_pipeline_func(request):
    print("pipeline_increase_job_size: Starting")
    pipeline_name = request.args.get("pipeline_name")
    bifrost_instance = request.args.get("bifrost_instance")
    processing_step_nr = request.args.get("processing_step_nr")
    if not pipeline_name or not bifrost_instance or not processing_step_nr:
        return jsonify(
            {"error": "pipeline_name, bifrost_instance and processing_step_nr required"}), 400
    try:
        res = increaseJobSize_pipeline(pipeline_name, bifrost_instance, int(processing_step_nr))
        print("pipeline_increase_job_size: Completed")
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#"/api/userStatus"
def extract_userStatus_func(request):
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

#return app
# Instance for gunicorn "app.main:app"
#Da mutare perche se no il batch non funziona
#app = create_app()
#ensure_valid_login() #Manage login after creating the app
#ensure_valid_pipeline_id(None, "create_app", REFRESH_INTERNAL_PIPELINE_ID, False)  #Refresh pipeline.json the first run of the day
#print("Login completed, calls can be made now")