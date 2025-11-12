import os

from legacy.WebService.WSPipelineRerun import simpleRerun, pipeline_rerun
from legacy.WebService.WSPipelineRerun import pipeline_rerun
from legacy.WebService.WSManageLogin import visualfabriq_login
from legacy.WebService.WSPipelineRuntime import scrape_pipeline_last_run
from legacy.WebService.WSstatusScraper import scrape_pipeline_status
from legacy.WebService.WSLogExtractor import log_extractor
from legacy.WebService.WSFullExtractor import full_extractor
from legacy.WebService.WSUserStatus import scrape_user_list
from legacy.WebService.WSPipelineFile import setFileMappingPy   #TODO TO REMOVE
from legacy.WebService.WSPipelineGetID import getID_pipelines
from legacy.WebService.WSPipelineIncreaseTimeout import pipeline_increase_timeout
from legacy.WebService.WSPipelineIncreaseJobSize import pipeline_increase_job_size

STATE_PATH = os.getenv("STATE_PATH", "legacy/WebService/state.json")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true" #TOCHANGE TRUE #DEBUGGGING

#Login management function
def login_and_cache_state(organisationId: str, email: str, password: str) -> dict:
    print("Starting login_and_cache_state function")
    visualfabriq_login(organisationId, email, password)
    return {"status": "ok", "state_path": STATE_PATH}

#Pipeline rerun function, CLICCA IL PULSANTE DI RERUN SOLTANTO
def rerun_pipeline(pipeline_id: str, bifrost_instance: str) -> dict:
    print("Starting rerun_pipeline function")
    simpleRerun(pipeline_id, bifrost_instance, HEADLESS)
    return {"pipeline": pipeline_id, "started": True}

#Pipeline complete rerun function, RERUN COMPLETO CON SPOSTAMENTO DEL FILE
def complete_rerun_pipeline(pipeline_id: str, bifrost_instance: str) -> dict:
    print("Starting complete_rerun_pipeline function")
    pipeline_rerun(pipeline_id, bifrost_instance, HEADLESS)
    return {"pipeline": pipeline_id, "started": True}

#Pipeline runtime function
def runtime_pipeline(pipeline_id: str, bifrost_instance: str) -> dict:
    print("Starting runtime_pipeline function")
    res = scrape_pipeline_last_run(pipeline_id, bifrost_instance, HEADLESS)
    return res


#Pipeline ID function
def getID_pipeline(bifrost_instance: str, filterEnabled: bool = False) -> dict:
    print(f"Updating pipeline id for instance: {bifrost_instance}")
    res = getID_pipelines(bifrost_instance, filterEnabled, HEADLESS)
    return res

#Pipeline status function
def status_pipeline(status_filter: bool, bifrost_instance: str) -> dict:
    print("Starting status_pipeline function")
    res = scrape_pipeline_status(bifrost_instance, status_filter, HEADLESS)
    return res

#Pipeline last log download function
def log_pipeline(pipeline_id: str, bifrost_instance: str) -> dict:
    print("Starting log_pipeline function")
    res= log_extractor(pipeline_id, bifrost_instance, HEADLESS)
    return res

#Pipeline full extract function
def fullExtract_pipeline(status_filter: str, bifrost_instance: str) -> dict:
    print("Starting fullExtract_pipeline function")
    res = full_extractor(bifrost_instance, status_filter, HEADLESS)
    return res


#Visualfabriq User status function
def extract_userStatus(bifrost_instance: str):
    print("Starting extract_userStatus function")
    res, vf_instance = scrape_user_list(bifrost_instance, HEADLESS)
    return res, vf_instance

#Pipeline timeout increase function
def increaseTimeout_pipeline(pipeline_name: str, bifrost_instance: str, delta_increase: int, processing_step_nr: int) -> dict:
    print("Starting increaseTimeout_pipeline function")
    res = pipeline_increase_timeout(pipeline_name, bifrost_instance, delta_increase, processing_step_nr, HEADLESS)
    return res

#Pipeline job size increase function
def increaseJobSize_pipeline(pipeline_name: str, bifrost_instance: str, processing_step_nr: int) -> dict:
    print("Starting increaseTimeout_pipeline function")
    res = pipeline_increase_job_size(pipeline_name, bifrost_instance, processing_step_nr, HEADLESS)
    return res