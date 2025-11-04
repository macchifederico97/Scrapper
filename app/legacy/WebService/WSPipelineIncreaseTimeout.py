from playwright.sync_api import sync_playwright


def pipeline_increase_timeout(pipeline_filter: str, bifrost_instance: str, deltaIncrease: int, processingStepNr: int, headlessPar:bool):
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
        page.wait_for_timeout(2000)
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
        page.locator('text="Timeout"').wait_for(state="visible")
        currentTimeout = page.locator(".bifrostcss-cGCXgx").nth(4).input_value()
        updatedTimeout = int(currentTimeout) + deltaIncrease
        page.locator(".bifrostcss-cGCXgx").nth(4).fill(str(updatedTimeout))

        #HO MODIFICATO IL TIMEOUT, CLICCO SUL PULSANTE DI UPDATE #TODO
        page.locator(".bifrostcss-gFcKFW").nth(2).click()
        page.wait_for_timeout(2000)

        print(f"Pipeline {pipeline_filter} timeout successfully increased by {deltaIncrease} seconds; current timeout is {updatedTimeout} seconds")
        return {"pipeline_name":pipeline_filter, "old_timeout": currentTimeout, "new_timeout": updatedTimeout}




#print(pipeline_increase_timeout("Claim Inbound Import & Process", "nttdata", 3600, 1, False))  #TEST & DEBUGGING