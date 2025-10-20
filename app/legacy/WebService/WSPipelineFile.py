from datetime import datetime
from playwright.sync_api import sync_playwright
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

    page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")

    page.wait_for_load_state()
    page.wait_for_timeout(8000)

    if statusFilter == True:
        filter_status_enabled(page)

    exit_loop = False
    while not exit_loop:
        elements = page.locator(".bifrostcss-eXwpzm.undefined")
        count = elements.count()

        if count == 0:
            break

        first_pipeline_name = elements.nth(0).inner_text()
        if first_pipeline_name in pipelineNames:
            break  # Already visited this page

        for i in range(count):
            element = elements.nth(i)
            pipeline_name = element.inner_text()
            pipelineNames.append(pipeline_name)

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

    # Click pipeline elements
    page.locator(".bifrostcss-fFaJCf").nth(6).click()  #Opening the pipeline history            

    page.wait_for_load_state()
    page.wait_for_timeout(2000)     #TEST

    pipelineID = page.url.split("/")[-2]

    page.locator(".bifrostcss-fIrYkC").click()  #Pipeline-history page close
    page.wait_for_timeout(3000)


    return pipelineName, pipelineID


def setFileMappingPy(bifrost_instance: str, headlessPar: bool):
    """
    Scrapes the last pipeline execution filtered by name.
    Returns a dictionary with start time, finish time, and duration in minutes.
    """

    # OPENING BROWSER
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headlessPar
            , args=["--no-sandbox", "--ignore-certificate-errors"])
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        pipelineNames = getPipelineNames(page, bifrost_instance, True)  #Getting the names of all the pipelines in Bifrost

        outputList = [] #Output list containing pipeline information dict

        # Go to the page
        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")

        for pipelineName in pipelineNames:
                pipelineName, pipelineID = getPipelineID(pipelineName, page)
                pipeDict = {"pipeline_name": pipelineName, "pipeline_id": pipelineID}
                outputList.append(pipeDict)     #Creation of the dict with pipeline information and appended to the output list
        browser.close()

        # Save output to JSON file

        # Percorso completo
        cartella = Path(f"client/{bifrost_instance}")
        cartella.mkdir(parents=True, exist_ok=True)
        file_path = cartella / "pipeline.json"
        
        # Timestamp ISO 8601
        timestamp = datetime.now().isoformat(timespec="seconds")

        # Struttura finale
        fileData = {
            "last_updated": timestamp,
            "pipelines": outputList
        }

        # Scrittura
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(fileData, f, indent=4)

        return outputList


#print(setFileMappingPy("nttdata", False))    #DEBUG & TESTING