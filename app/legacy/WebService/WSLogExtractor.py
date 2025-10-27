import os
import csv
import json
from playwright.sync_api import sync_playwright

def log_extractor(pipeline_filter: str, bifrost_instance: str, headlessPar: bool):
    """
    Downloads the last log of the pipeline
    """
    script_dir = os.path.dirname(os.path.abspath(__file__)) #PATH ATTUALE DELLO SCRIPT
    download_dir = os.path.join(script_dir, "log")  #DOWNLOAD PATH
    os.makedirs("log", exist_ok=True)   #CREATE THE LOG DOWNLOAD FOLDER IF IT DOES NOT EXIST

    with sync_playwright() as p:
        # Launch browser (using Chrome already installed)
        browser = p.chromium.launch(
            headless=headlessPar  # Does not open a window    #DEBUGGING
        , args=["--no-sandbox", "--ignore-certificate-errors"])
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        #GET PIPELINE ID
        with open(f"client/{bifrost_instance}/pipeline.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        pipeline_id = None
        flIdFound = False
        for item in data["pipelines"]:
            if item["pipeline_name"] == pipeline_filter:
                pipeline_id = item["pipeline_id"]
                flIdFound = True
                break

        if flIdFound:
            # AUTO SEARCH TRAMITE PIPELINE_ID NEL DATABASE
            ''' #NON HO BISOGNO DELLA GENERAL SEARCH UNA VOLTA TROVATO IL PIPELINE ID
            page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")
            page.wait_for_load_state()
            page.wait_for_timeout(6000)
            '''

            # Filter pipeline
            page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines/{pipeline_id}/history")
            page.wait_for_load_state()
            page.wait_for_timeout(1000)
        else:
           # MANUAL SEARCH, PIPELINE_ID NOT FOUND NEL DATABASE
            print(f"Pipeline {pipeline_filter} not found, doing manual search")
            page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")
            page.wait_for_load_state()
            page.wait_for_timeout(6000)

            # Filter pipeline
            page.get_by_placeholder("Search by name...").type(pipeline_filter)
            page.wait_for_timeout(3000)

            if page.locator(".bifrostcss-eXwpzm.undefined").count() == 0:
                return "pipelineNotFound"  # error raised if no pipeline has been found

            page.locator(".bifrostcss-fFaJCf").nth(6).click()  #CLICK ON THE PIPELINE HISTORY
            page.wait_for_timeout(500)

            #URL CHECK
            if "/history" in page.url:
                print("correct URL!")
            else:
                print("Uncorrect URL:", page.url)
                # Vai su una pipeline con /steps

                # Cambia URL a /history senza ricaricare
                page.evaluate("""
                               const path = window.location.pathname;
                               const base = path.substring(0, path.lastIndexOf('/'));
                               const nuovaUrl = base + '/history';
                               window.history.pushState({}, '', nuovaUrl);
                           """)
                page.wait_for_timeout(2000)

        page.locator(".bifrostcss-bnFVuH").nth(0).click()  #CLICK ON THE LAST EXECUTION
        page.wait_for_timeout(500)

        #CLICK ON THE DOWNLOAD LOG BUTTON
        if page.locator(".bifrostcss-hVuvHH").count() == 0: #HANDLE THE CASE WHERE I HAVE NO LOG FOR THE PIPELINE
            print("No log found for pipeline: " + str(pipeline_filter)) #DEBUGGING
            return "LogNotFound"

        outputList = []

        for i in range(page.locator(".bifrostcss-hVuvHH").count()): #TO HANDLE THE CASE OF WHEN AN EXECUTION HAS MORE THAN ONE LOG
            with page.expect_download() as download_info:
                page.locator(".bifrostcss-hVuvHH").nth(i).click()   #CLICK THE DOWNLOAD LOG BUTTON
                print("Downloading log nr: " + str(i + 1)) #DEBUGGING

                download = download_info.value
                save_path = os.path.join(download_dir, download.suggested_filename)

                download.save_as(save_path)
                print(f"Download nr.{i + 1} finished")  #DEBUGGING

                #OUTPUT MANAGEMENT
                with open(save_path, newline="", encoding="utf-8") as file:
                    iter=0
                    reader = csv.DictReader(file)
                    fileDict = {}   #SAVE THE CONTENT OF THE DOWNLOADED LOG IN A DICT
                    for row in reader:
                        iter+=1
                        fileDict[row["timestamp"]+str(iter % 100).zfill(3)] = row["message"]
                    outputList.append(fileDict) #INSERT THE DICT INTO THE OUTPUT LIST


        page.wait_for_timeout(3000)
        # Cleanup browser
        context.close()
        browser.close()


        for filename in os.listdir("log"):
            file_path = os.path.join("log", filename)
            if os.path.isfile(file_path):  #delete only files
                os.remove(file_path)

        return outputList
        #return save_path, download.suggested_filename

print(log_extractor("Demand - Export forecast", "nttdata", False)) #TEST & DEBUGGING