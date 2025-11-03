from datetime import datetime
#from legacy.WebService.WSPipelineGetID import getID_pipelinesù
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import sys

#TODO DA RIMUOVERE

sys.path.insert(0, "legacy/WebService")
from WSPipelineGetID import getID_pipelines
sys.path.pop(0)

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

    if statusFilter == True:
        filter_status_enabled(page)
    else:
        page.wait_for_timeout(5000)
        
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
    #page.wait_for_timeout(2000)     #TEST

    pipelineID = page.url.split("/")[-2]

    page.locator(".bifrostcss-fIrYkC").click()  #Pipeline-history page close
    page.wait_for_timeout(2000)


    return pipelineName, pipelineID


def setFileMappingPy(bifrost_instance: str, filterEnabled: bool, headlessPar: bool):
    """
    Scrapes the last pipeline execution filtered by name.
    Returns a dictionary with start time, finish time, and duration in minutes.
    """
    print("Starting setFileMappingPy function")
    return getID_pipelines(bifrost_instance, filterEnabled,  headlessPar)


#print(setFileMappingPy("nttdata", False))    #DEBUG & TESTING