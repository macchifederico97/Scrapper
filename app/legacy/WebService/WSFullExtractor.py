import json
from playwright.sync_api import sync_playwright
from datetime import datetime





def full_extractor(bifrost_instance: str, filter_enabled: str, headlessPar: bool):
    """
    Extracts full infos from all the pipelines in the system.
    Returns a message describing the result.
    """

    def getPipelineInformations(pipelineName: str, id_pipeline):  #Lightweight function of scrape_pipeline_last_run from WSPipelineRuntime
        page.wait_for_load_state()
        print(f"L'ID della pipeline '{pipelineName}' è: {id_pipeline}")

        if "/pipeline" in page.url:
            page.evaluate(f"""
                const path = window.location.pathname.split("pipeline")[0] + "pipelines";
                const nuovaUrl = path + '/{id_pipeline}/history';
                window.history.pushState({{}}, '', nuovaUrl);
            """)

            page.wait_for_timeout(2000)

        
        schedule = page.locator(".bifrostcss-gSjZro").nth(6).inner_text()

        page.wait_for_load_state()
        page.wait_for_timeout(2000)     #TEST

        if page.locator(".bifrostcss-bnFVuH").count() == 0:     #Handling the case where the pipeline has never been runned
            page.locator(".bifrostcss-fIrYkC").click()  # Pipeline-history page close
            page.wait_for_timeout(1000)
            return "", "", "", ""

        page.locator(".bifrostcss-bnFVuH").nth(0).click()  # last execution
        page.wait_for_timeout(500)

        # Extract start and finish times (as strings from the page)
        startTime = page.locator(".bifrostcss-bItxDa").nth(0).inner_text()
        finishTime = page.locator(".bifrostcss-bItxDa").nth(1).inner_text()
        page.wait_for_timeout(500)

        page.locator(".bifrostcss-fIrYkC").click()  #Pipeline-history page close
        page.wait_for_timeout(1000)

        #CALCOLO IL RUNTIME
        dt_format = "%m/%d/%Y, %I:%M:%S %p %Z"
        start_dt = datetime.strptime(startTime, dt_format)
        finish_dt = datetime.strptime(finishTime, dt_format)
        duration_minutes = (finish_dt - start_dt).total_seconds() / 60.0

        return startTime, finishTime, duration_minutes, schedule




    #pipelineStatusDict = scrape_pipeline_status(bifrost_instance=bifrost_instance, filter_enabled=filter_enabled, headlessPar= headlessPar)   #Getting a dict with all the pipelines and their last run status
    #pipelineNames = pipelineStatusDict.keys()   #Getting the names of all the pipelines in Bifrost

    outputList = [] #Output list containing pipeline information dict

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headlessPar
        , args=["--no-sandbox", "--ignore-certificate-errors"])
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        # Go to the page
        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")
        print("Page loaded")

        # Lettura dal file
        with open(f"client/{bifrost_instance}/pipeline.json", "r", encoding="utf-8") as f:
            pipelines = json.load(f)
        print(f"Loaded {len(pipelines)} pipelines from JSON file.")
        for pipeline in pipelines["pipelines"]:
                startTime, finishTime, duration_minutes, schedule = getPipelineInformations(pipeline["pipeline_name"], pipeline["pipeline_id"])
                pipeDict = {"pipeline_name": pipeline["pipeline_name"], "status": "valid test", "start_time": startTime,
                        "finish_time": finishTime, "duration_minutes": duration_minutes, "schedule": schedule}
                outputList.append(pipeDict)     #Creation of the dict with pipeline information and appended to the output list

        browser.close()
        return outputList


#print(full_extractor(bifrost_instance="nttdata", filter_enabled="false"))    #TEXT/DEBUGGING