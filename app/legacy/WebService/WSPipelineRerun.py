from playwright.sync_api import sync_playwright
import os

#FUNZIONE ESPOSTA, RERUN COMPLETO CON SPOSTAMENTO DEL FILE
#TODO AGGIUNGERE CREAZIONE DI FOLDER IN IMPORT QUEUE IN CASO DI FOLDER NON TROVATA
def pipeline_rerun(pipeline_filter: str, bifrost_instance: str, headlessPar: bool) -> str:
    """
    Clicks the execute button for the pipeline in input
    """
    with sync_playwright() as p:
        # Launch browser (using Chrome already installed)
        browser = p.chromium.launch(
            headless=headlessPar  # Does not open a window    #DEBUGGING
        , args=["--no-sandbox", "--ignore-certificate-errors"])
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})
        
        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")
        page.wait_for_timeout(5000)
        
        #Filter pipeline
        filterPipelineByName(page, pipeline_filter) 

        page.locator(".bifrostcss-fFaJCf").nth(7).click()  #Opening the pipeline details page
        
        page.wait_for_timeout(5000)        #check if data staging is present

        #get staging file path
        results = getPathStagingFile(page, pipeline_filter, bifrost_instance) 
        
        #move files to import-queue
        for result in results:
            moveFilesToImportQueue(page, result, bifrost_instance) 
        
        #click Run pipeline
        clickButtonRun(page, bifrost_instance, pipeline_filter)

        # Cleanup browser
        context.close()
        browser.close()

        return pipeline_filter


def filterPipelineByName(page, pipeline_filter):
    page.locator('text="Name"').wait_for(state="visible")
    page.wait_for_load_state()
    #page.locator('text="Search by name..."').wait_for(state="visible")
    page.get_by_placeholder("Search by name...").type(pipeline_filter)
    page.wait_for_timeout(5000)


def clickButtonRun(page, bifrost_instance, pipeline_filter):  #Lightweight function of scrape_pipeline_last_run from WSPipelineRuntime
    page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")

    # Filter pipeline
    page.wait_for_load_state()
    page.get_by_placeholder("Search by name...").type(pipeline_filter)
    page.wait_for_timeout(3000)

    if page.locator(".bifrostcss-eXwpzm.undefined").count() == 0:
        return ""   #error raised if no pipeline has been found

    # Click pipeline elements
    page.locator(".bifrostcss-fFaJCf").nth(4).click()   #click on the execute button
    page.wait_for_timeout(3000)


def getPathStagingFile(page, pipeline_filter: str, bifrost_instance: str):
    staging_elements = page.locator('text=/^Data Staging$/')

    count = staging_elements.count()
    if count == 0:  # GESTISCO IL CASO IN CUI LA PIPELINE NON E DI PROCESSING
        print(f"Pipeline {pipeline_filter} doesn't contain any processing steps")  # DEBUGGING
        return f"Pipeline {pipeline_filter} doesn't contain any processing steps"
    results = []
    for i in range(count):
        # Clicca sull'elemento i-esimo
        staging_elements.nth(i).click()
        page.locator('text="Import Folder"').wait_for(state="visible")
        path = page.locator(".bifrostcss-cGCXgx").nth(3).input_value()
        format = page.locator(".bifrostcss-iFEVQl").nth(2).text_content()
        if format == "excel":   #GESTISCO IL CASO DI EXCEL, DOVE FORMAT NON E UGUALE ALL'ESTENSIONE DEL FILE
            format = "xlsx"
        print(f"Import Folder Path: {path}, Format: {format}")
        results.append({"path": path, "format": format})

        page.locator(".bifrostcss-iRNFVM").nth(0).click()   #RITORNO ALLA PAGINA DEGLI STEP DELLA PIPELINE
        page.wait_for_timeout(500)
    return results
    
#SPOSTA SEMPRE IL PRIMO FILE TROVATO IN ALTO, IN ORDINE DECRESCENTE DI CARICAMENTO
def moveFilesToImportQueue(page, result, bifrost_instance):
    page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/files/vf-import-processed/{result['path']}")
    page.locator('text="vf-import-processed"').wait_for(state="visible")
    page.wait_for_timeout(2000)
    if page.locator('.bifrostcss-ieEbAG').is_visible():
        print("No files found in" , result['path'])
    else:
        print("Files found in" , result['path'])
        page.get_by_placeholder("Search").nth(0).fill(result['format'])
        page.wait_for_timeout(3000)

        #ORDINO I FILE PER ORDINE DECRESCENTE DI UPLOAD
        page.locator(".bifrostcss-qqsxH").nth(3).click()
        page.wait_for_timeout(500)
        page.locator(".bifrostcss-qqsxH").nth(3).click()
        page.wait_for_timeout(500)


        print(page.locator(".bifrostcss-edwLhL").count())
        # Move files to import-queue
        if page.locator(".bifrostcss-edwLhL").count() > 1:
            page.locator(".bifrostcss-edwLhL").nth(1).click() #flag
            page.wait_for_timeout(1000)
            page.click('text="Move file(s)"')
            page.wait_for_timeout(3000)
            page.locator('.bifrostcss-dSqOgl').nth(1).locator('.bifrostcss-WnhIC').nth(0).click()
            page.wait_for_timeout(3000)

            page.click('text="vf-import-queue"')

            page.locator('text="Moving files to:"').wait_for(state="visible")
            # Cycle on each folder
            for folder in result['path'].split("/"):
                page.get_by_placeholder("Search").nth(1).fill(folder)
                page.wait_for_timeout(3000)
                page.locator(".bifrostcss-WnhIC").last.click()

            page.click('text="Move"')
        else:
            print("No files with format" , result['format'] , "found in" , result['path'])


#FUNZIONE ESPOSTA DEL SIMPLE RERUN, CLICCA IL PULSANTE DI RERUN DATA LA PIPELINE
def simpleRerun(pipeline_filter, bifrost_instance, headlessPar: bool):
    with sync_playwright() as p:
        # Launch browser (using Chrome already installed)
        browser = p.chromium.launch(
            headless=headlessPar  # Does not open a window    #DEBUGGING
            , args=["--no-sandbox", "--ignore-certificate-errors"])
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")

        # Filter pipeline
        page.wait_for_load_state()
        page.get_by_placeholder("Search by name...").type(pipeline_filter)
        page.wait_for_timeout(3000)

        if page.locator(".bifrostcss-eXwpzm.undefined").count() == 0:
            return f"Error: Pipeline {pipeline_filter} not found"   #error raised if no pipeline has been found

        # Click pipeline elements
        page.locator(".bifrostcss-fFaJCf").nth(4).click()   #click on the execute button
        page.wait_for_timeout(3000)
        return f"Pipeline {pipeline_filter} rerunned successfully"

#print(pipeline_rerun("Import Baseline", "nttdata", False))  #TEST & DEBUGGING