from datetime import datetime
from playwright.sync_api import sync_playwright
#from WSstatusScraper import scrape_pipeline_status
#from WSstatusScraper import _filter_status_enabled
#from datetime import datetime
from pathlib import Path
import json

#FUNCTION THAT RETURNS THE NAME AND ID OF ALL PIPELINES IN THE SYSTEM
def getPipelineNames(page, bifrost_instance:str, statusFilter: bool): 
    def filter_status_enabled(page):
        """
        Applies the 'Pipeline Status = Enabled' filter on the page.
        """
        page.wait_for_load_state()
        page.click("text=Filters")
        page.wait_for_timeout(500)

        page.locator(".bifrostcss-JgNqY").nth(2).click()
        page.wait_for_timeout(500)
        page.locator(".bifrostcss-eGauau").nth(2).click()
        page.wait_for_timeout(500)
        page.locator(".bifrostcss-JgNqY").nth(3).click()
        page.wait_for_timeout(500)
        page.locator(".bifrostcss-eGauau").nth(0).click()
        page.wait_for_timeout(500)

        page.click("text=Apply")
        page.wait_for_timeout(1000)

    pipelineNames = []  #FUNCTION OUTPUT LIST
    checkpipelineNames = []  #FUNCTION OUTPUT CHECK LIST

    page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")

    page.wait_for_load_state()
    page.wait_for_timeout(8000)

    if statusFilter == True:
        filter_status_enabled(page)
    
    page.wait_for_timeout(20000)
    page.wait_for_load_state()
    exit_loop = False
    while not exit_loop:
        elements_name = page.locator(".bifrostcss-eXwpzm.undefined")
        elements_status_schedule = page.locator(".bifrostcss-kcyQxi")

        count = elements_name.count()

        if count == 0:
            break

        first_pipeline_name = elements_name.nth(0).inner_text()
        if first_pipeline_name in checkpipelineNames:
            break  # Already visited this page

        for i in range(count):
            element_name = elements_name.nth(i).inner_text()
            element_schedule = elements_status_schedule.nth(i).locator("td").nth(6).inner_text()
            element_status = elements_status_schedule.nth(i).locator("td").nth(2).inner_text()

            pipiline_ID = page.locator("a[href*='/pipelines/'][href*='history']").nth(i).get_attribute("href").split("pipelines/")[1].split("/")[0]
            print(element_name + " - " + pipiline_ID + " - " + element_schedule + " - " + element_status)
            pipelineNames.append(element_name + " -- " + pipiline_ID + " -- " + element_schedule + " -- " + element_status)
            checkpipelineNames.append(element_name)

        # Go to next page
        page.click("text=Next")
        page.wait_for_load_state()
        page.wait_for_timeout(2000)

    return pipelineNames


def getPipelineID(pipelineName: str, page):  #Lightweight function of scrape_pipeline_last_run from WSPipelineRuntime
    page.wait_for_load_state()
    page.get_by_placeholder("Search by name...").fill(pipelineName)
    page.wait_for_timeout(2000) #TEST

    if page.locator(".bifrostcss-eXwpzm.undefined").count() == 0:
        return "pipeline not found", "pipeline not found", "pipeline not found", "pipeline not found"   #error raised if no pipeline has been found

    #Retrieve pipeline schedule and status 
    status = page.locator(".bifrostcss-gSjZro").nth(2).inner_text()
    schedule = page.locator(".bifrostcss-gSjZro").nth(6).inner_text()

    # Click pipeline elements
    page.locator(".bifrostcss-fFaJCf").nth(6).click()  #Opening the pipeline history            

    page.wait_for_load_state()
    page.wait_for_timeout(2000)     #TEST

    pipelineID = page.url.split("/")[-2]

    page.locator(".bifrostcss-fIrYkC").click()  #Pipeline-history page close
    page.wait_for_timeout(3000)


    return pipelineName, pipelineID, schedule, status


def getID_pipelines(bifrost_instance: str, filterEnabled: bool, headlessPar: bool):
    """
    Scrapes the last pipeline execution filtered by name.
    Returns a dictionary with start time, finish time, and duration in minutes.
    """
    print("Starting getID_pipelines function")
    # OPENING BROWSER
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headlessPar
            , args=["--no-sandbox", "--ignore-certificate-errors"])
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        pipelineNames = getPipelineNames(page, bifrost_instance, filterEnabled)  #Getting the names of all the pipelines in Bifrost

        outputList = [] #Output list containing pipeline information dict

        # Go to the page
        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")

        countPipelines = len(pipelineNames)
        count = 0
        print(f"Total pipelines found: {countPipelines}")

        for pipelineName in pipelineNames:
                print(f"Processing pipeline: {pipelineName}")
                count += 1
                print(f"Progress: {count}/{countPipelines}")
                print(count)
                pipelineName, pipelineID, schedule, status = pipelineName.split(" -- ", 3)
                pipeDict = {"pipeline_name": pipelineName, "pipeline_id": pipelineID, "schedule": schedule, "status": True if status == "Enabled" else False}
                outputList.append(pipeDict)     #Creation of the dict with pipeline information and appended to the output list
        browser.close()

        # Save output to JSON file

        # Complete path
        cartella = Path(f"client/{bifrost_instance}")
        cartella.mkdir(parents=True, exist_ok=True)
        file_path = cartella / "pipeline.json"

        # Timestamp ISO 8601
        timestamp = datetime.now().isoformat(timespec="seconds")
        
        fileData = {
            "last_updated": timestamp,
            "pipelines": outputList
        }
        # Scrittura
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(fileData, f, indent=4)

        #OUTPUT FILE TESTING
        nome_cercato = "TTR - Contracts Status update"

        # Reading from file
        with open(f"client/{bifrost_instance}/pipeline.json", "r", encoding="utf-8") as f:
            pipelines = json.load(f)

        # ID Extraction
        id_pipeline = next((p["pipeline_id"] for p in pipelines["pipelines"] if p["pipeline_name"] == nome_cercato), None)
        print(f"L'ID della pipeline '{nome_cercato}' è: {id_pipeline}")
        #END OF OUTPUT FILE TESTING

        return outputList


#print(getID_pipelines("nttdata",true, False))    #DEBUG & TESTING