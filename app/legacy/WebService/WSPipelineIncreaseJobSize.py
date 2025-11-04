from playwright.sync_api import sync_playwright

#ARRAY CONTENENTE TUTTI I JOB SIZE SELEZIONABILI, ORDINATI PER DIMENSIONE
jobSizeArray = ["Micro (2 GB)", "Small (4 GB)", "Medium (8 GB)", "Large (30 GB)", "XLarge (64 GB)", "XXLarge (120 GB)"]

def pipeline_increase_job_size(pipeline_filter: str, bifrost_instance: str, processingStepNr: int, headlessPar:bool):
    with sync_playwright() as p:
        # Launch browser (using Chrome already installed)
        browser = p.chromium.launch(
            headless=headlessPar  # Does not open a window    #DEBUGGING
            , args=["--no-sandbox", "--ignore-certificate-errors"]
            #, executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        )
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        #MI SPOSTO SUGLI STEP DELLA PIPELINE
        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")
        page.get_by_placeholder("Search by name...").type(pipeline_filter)
        page.wait_for_timeout(3000)
        page.locator(".bifrostcss-fFaJCf").nth(7).click()  # CLICK ON THE PIPELINE STEPS
        page.wait_for_timeout(1000)

        #CALCOLO IL NUMERO DI PROCESSING
        staging_elements = page.locator('text=/^Data Processing$/')
        count = staging_elements.count()
        if count == 0:  #GESTISCO IL CASO IN CUI LA PIPELINE NON E DI PROCESSING
            print(f"Pipeline {pipeline_filter} doesn't contain any processing steps")   #DEBUGGING
            return f"Pipeline {pipeline_filter} doesn't contain any processing steps"
        if processingStepNr > count:    #GESTISCO IL CASO IN CUI IL PROCESSING STEP IN INPUT NON E CONTENUTO NELLA PIPELINE
            print(f"Pipeline {pipeline_filter} doesn't have {processingStepNr} processing steps")   #DEBUGGING
            return f"Pipeline {pipeline_filter} doesn't have {processingStepNr} processing steps"
        page.locator('text=/^Data Processing$/').nth(processingStepNr - 1).click()

        #SONO ENTRATO NELLA PAGINA DI CUSTOMIZZAZIONE DEL PROCESSING STEP DELLA PIPELINE
        page.locator('text="Job size"').wait_for(state="visible")
        dropdownSelector = page.locator(".bifrostcss-iTGHxx").nth(2) #HO PRESO IL SELECTOR JOB SIZE
        #dropdownSelector.click()    #DEUBGGING
        currentOption = dropdownSelector.inner_text() #PRENDO IL TESTO ATTUALE PRESENTE NEL JOB SIZE

        newOption = jobSizeArray[jobSizeArray.index(currentOption) + 1]     #PRENDO L'ELEMENTO CON MEMORIA SUBITO SUPERIRE AL JOB SIZE ATUALE

        dropdownSelector.click()    #APRO IL MENU A TENDINA CON I JOB SIZE
        page.wait_for_timeout(500)

        page.get_by_text(newOption, exact=True).click()     #CLICCO SULLA NUOVA OPZIONE

        #HO MODIFICATO IL TIMEOUT, CLICCO SUL PULSANTE DI UPDATE #TODO
        page.locator(".bifrostcss-gFcKFW").nth(2).click()
        page.wait_for_timeout(2000)

        print(f"Pipeline {pipeline_filter} job size successfully increased from {currentOption} to {newOption}")
        return {"pipeline_name": pipeline_filter, "old_job_size": currentOption, "new_job_size": newOption}


#print(pipeline_increase_job_size("Claim Inbound Import & Process", "nttdata", 1, False))  #TEST & DEBUGGING