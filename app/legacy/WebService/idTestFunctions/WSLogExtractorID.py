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
    os.makedirs("log", exist_ok=True)   #CREO LA CARTELLA DI DOWNLOAD DEI LOG SE NON ESISTE

    with sync_playwright() as p:
        # Launch browser (using Chrome already installed)
        browser = p.chromium.launch(
            headless=headlessPar  # Does not open a window    #DEBUGGING
        , args=["--no-sandbox", "--ignore-certificate-errors"])
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        #GET PIPELINE ID
        with open("pipeline.json", "r") as file:    #TODO CAMBIARE PATH
            data = json.load(file)

        pipeline_id = None
        flIdFound = False
        for item in data:
            if item["pipeline_name"] == pipeline_filter:
                pipeline_id = item["pipeline_id"]
                flIdFound = True
                break

        if flIdFound:
            # MANUAL SEARCH, PIPELINE_ID NOT FOUND NEL DATABASE
            page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")
            page.wait_for_load_state()
            page.wait_for_timeout(6000)

            # Filter pipeline
            page.get_by_placeholder("Search by name...").type(pipeline_filter)
            page.wait_for_timeout(3000)

            if page.locator(".bifrostcss-eXwpzm.undefined").count() == 0:
                return "pipelineNotFound"  # error raised if no pipeline has been found

            page.locator(".bifrostcss-fFaJCf").nth(6).click()  # CLICCO SULLO STORICO DELLA PIPELINE
            page.wait_for_timeout(500)
        else:
            # AUTO SEARCH TRAMITE PIPELINE_ID NEL DATABASE
            page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines/{pipeline_id}/history")
            page.wait_for_load_state()
            page.wait_for_timeout(6000)

            if page.locator(".bifrostcss-bnFVuH").count()==0:   #GESTISCO IL CASO IN CUI NON TROVO LA PIPELINE
                return "PipelineNotfound"

        page.locator(".bifrostcss-bnFVuH").nth(0).click()  # CLICCO SULL'ULTIMA ESECUZIONE
        page.wait_for_timeout(500)

        #CLICCARE SUL PULSANTE DOWNLOAD LOG

        if page.locator(".bifrostcss-hVuvHH").count() == 0: #GESTISCO IL CASO IN CUI NON HO LOG PER LA PIPELINE
            print("No log found for pipeline: " + str(pipeline_filter)) #DEBUGGING
            return "LogNotFound"

        outputList = []

        for i in range(page.locator(".bifrostcss-hVuvHH").count()): #PER GESTIRE IL CASO DI QUANDO UN ESECUIONE HA PIU LOG
            with page.expect_download() as download_info:
                page.locator(".bifrostcss-hVuvHH").nth(i).click()   #CLICCO IL PULSANTE DOWNLOAD LOG
                print("Downloading log nr: " + str(i + 1)) #DEBUGGING

                download = download_info.value
                save_path = os.path.join(download_dir, download.suggested_filename)

                download.save_as(save_path)
                print(f"Download nr.{i + 1} finished")  #DEBUGGING

                #GESTIONE DELL'OUTPUT
                with open(save_path, newline="", encoding="utf-8") as file:
                    iter=0
                    reader = csv.DictReader(file)
                    fileDict = {}   #SALVO IL CONTENUTO DEL LOG SCARICATO IN UN DICT
                    for row in reader:
                        iter+=1
                        #print(row["timestamp"][:-3]+str(iter % 100).zfill(3))
                        fileDict[row["timestamp"]+str(iter % 100).zfill(3)] = row["message"]
                    outputList.append(fileDict) #INSERISCO IL DICT NELLA LISTA DI OUTPUT


        page.wait_for_timeout(3000)
        # Cleanup browser
        context.close()
        browser.close()


        for filename in os.listdir("log"):
            file_path = os.path.join("log", filename)
            if os.path.isfile(file_path):  # elimina solo i file
                os.remove(file_path)

        return outputList
        #return save_path, download.suggested_filename

#print(log_extractor("Demand - Refresh Trade Promotion within module Demand - Revenue Plan V2", "nttdata")) #TEST & DEBUGGING