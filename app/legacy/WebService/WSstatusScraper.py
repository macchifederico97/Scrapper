from playwright.sync_api import sync_playwright, TimeoutError
import json


# ----------------------------
# Main scraping function for API
# ----------------------------
def scrape_pipeline_status(bifrost_instance: str, filter_enabled: bool, headlessPar: bool):
    """
    Scrapes Bifrost pipelines and returns their last run status.
    Parameters:
        filter_enabled (bool): whether to filter for pipelines with status 'Enabled'
    Returns:
        dict: {pipeline_name: last_run_status}
    """

    outputList = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headlessPar,  # Use headless for webservice/API
        args=["--no-sandbox", "--ignore-certificate-errors"]
            #,executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        )
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        # GET PIPELINE ID
        with open(f"client/{bifrost_instance}/pipeline.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data["pipelines"]:  #ITERO PER TUTTE LE PIPELINE PRESENTI NEL DB
            pipeline_status_dict = {}   #CREO IL DICT DOVE SALVARE LE INFO DELLA PIPELINE
            pipelineStatus = item["status"]
            filter_enabled = str(filter_enabled).lower() == "true"
            if (pipelineStatus == "Enabled" and filter_enabled) or not filter_enabled:
                pipeline_id = item["pipeline_id"]
                page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines/{pipeline_id}/history")
                page.wait_for_load_state()
                try:
                    # Prova a cliccare sul primo elemento entro 8000 ms (8 secondi) #PER CONTROLLARE SE LA PAGINA E CARICATA
                    page.locator(".bifrostcss-bnFVuH").nth(0).wait_for(state="visible", timeout=8000)

                except TimeoutError:
                    # Se non viene trovato, passa avanti senza fare nulla
                    pass
                runStatuses = page.locator(".bifrostcss-kpbtZs")
                if runStatuses.count() == 0:
                    lastRunStatus = "Never Executed"
                else:
                    lastRunStatus = runStatuses.nth(0).inner_text()
                #HO OTTENUTO IL LAST RUN STATUS DELLA PIPELINE CHE STO ITERANDO
                pipeline_status_dict["pipeline_name"] = item["pipeline_name"]
                pipeline_status_dict["status"] = lastRunStatus
                print("Pipeline: " + str(item["pipeline_name"]) + "; Last Run Status: " + str(lastRunStatus))
                outputList.append(pipeline_status_dict)

    return outputList

#print(scrape_pipeline_status("nttdata", False, False))    #DEBUGGING & TEST