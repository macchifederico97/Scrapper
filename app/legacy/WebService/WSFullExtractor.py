import json
from playwright.sync_api import sync_playwright, TimeoutError
from datetime import datetime


#PIPELINE NAME DONE
#STATUS
#START TIME
#FINISH TIME
#RUNTIME
#SCHEDULE DONE
def full_extractor(bifrost_instance: str, filter_enabled: str, headlessPar: bool):
    """
    Extracts full infos from all the pipelines in the system.
    Returns a message describing the result.
    """

    def getPipelineInformations(pipelineName: str, id_pipeline):  #Lightweight function of scrape_pipeline_last_run from WSPipelineRuntime
        page.wait_for_load_state()
        print(f"L'ID della pipeline '{pipelineName}' è: {id_pipeline}")

        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines/{id_pipeline}/history")

        page.wait_for_load_state()
        try:    #FOR QUICK LOAD CHECK
            # Prova a cliccare sul primo elemento entro 8000 ms (8 secondi) #PER CONTROLLARE SE LA PAGINA E CARICATA
            page.locator(".bifrostcss-bnFVuH").nth(0).wait_for(state="visible", timeout=8000)

        except TimeoutError:
            # Se non viene trovato, passa avanti senza fare nulla
            pass



        if page.locator(".bifrostcss-bnFVuH").count() == 0:     #Handling the case where the pipeline has never been runned
            return "", "", "", "Never Executed"

        page.locator(".bifrostcss-bnFVuH").nth(0).click()  # last execution
        page.wait_for_timeout(500)

        # Extract start and finish times (as strings from the page)
        status = page.locator(".bifrostcss-kpbtZs").nth(0).inner_text()
        startTime = page.locator(".bifrostcss-bItxDa").nth(0).inner_text()
        finishTime = page.locator(".bifrostcss-bItxDa").nth(1).inner_text()


        #CALCOLO IL RUNTIME
        dt_format = "%d/%m/%Y, %H:%M:%S %Z"
        start_dt = datetime.strptime(startTime, dt_format)
        finish_dt = datetime.strptime(finishTime, dt_format)
        duration_minutes = (finish_dt - start_dt).total_seconds() / 60.0
        print(f"{startTime}; {finishTime}; {duration_minutes} minutes; {status}")

        return startTime, finishTime, duration_minutes, status

    outputList = [] #Output list containing pipeline information dict

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headlessPar
        , args=["--no-sandbox", "--ignore-certificate-errors"]
        #, executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        )
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        # Go to the page
        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")
        print("Page loaded")

        # Lettura dal file
        with open(f"client/{bifrost_instance}/pipeline.json", "r", encoding="utf-8") as f:
            pipelines = json.load(f)
        filter_pipelines = filter_enabled.lower() == "true" if filter_enabled else False 
            
        for pipeline in pipelines["pipelines"]:
            if (filter_pipelines and pipeline["status"] != "Enabled"):
                continue

            else:
                print(f"Evaluating pipeline: {pipeline['pipeline_name']} with status {pipeline['status']}")
                print("---")
                print(f"Extracting info for pipeline: {pipeline['pipeline_name']}")
                schedule = pipeline["schedule"]
                startTime, finishTime, duration_minutes, status = getPipelineInformations(pipeline["pipeline_name"], pipeline["pipeline_id"])
                pipeDict = {"pipeline_name": pipeline["pipeline_name"], "status": status, "start_time": startTime,
                        "finish_time": finishTime, "duration_minutes": duration_minutes, "schedule": schedule}
                outputList.append(pipeDict)     #Creation of the dict with pipeline information and appended to the output list

        browser.close()
        return outputList


print(full_extractor(bifrost_instance="nttdata", filter_enabled="false", headlessPar=False))    #TEXT/DEBUGGING