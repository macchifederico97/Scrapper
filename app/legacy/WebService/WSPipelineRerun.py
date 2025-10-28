from playwright.sync_api import sync_playwright



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


        #get import folder ID
        # Filter pipeline
        #page.wait_for_timeout(3000)
        
        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")
        page.wait_for_timeout(5000)
        page.locator('text="Name"').wait_for(state="visible")
        page.wait_for_load_state()
        #page.locator('text="Search by name..."').wait_for(state="visible")
        page.get_by_placeholder("Search by name...").type(pipeline_filter)
        page.wait_for_timeout(3000)
        page.locator(".bifrostcss-fFaJCf").nth(7).click()  #Opening the pipeline details page
        
        page.wait_for_timeout(5000)        #check if data staging is present
        if page.locator('text=Staging').count()>0:
            page.locator('text="Data Staging"').wait_for(state="visible")
            page.click('text="Data Staging"')        
            page.locator('text="Import Folder"').wait_for(state="visible")
            path = page.locator(".bifrostcss-cGCXgx").nth(3).input_value()

            path = "test/test2"   #DEBUGGING
            # Go to the page
            page.goto(f"https://app.eu.visualfabriq.com/bifrost/nttdata/files/vf-import-processed/{path}")
            page.locator('text="vf-import-processed"').wait_for(state="visible")
            page.wait_for_timeout(3000)
            if page.locator('.bifrostcss-ieEbAG').is_visible():
                print("Folder is empty.")
            else:
                print("Folder contains files.")

                # Move files to import-queue
                page.locator(".bifrostcss-edwLhL").nth(1).click() #flag
                page.wait_for_timeout(1000)
                page.click('text="Move file(s)"')
                page.wait_for_timeout(3000)
                page.locator('.bifrostcss-dSqOgl').nth(1).locator('.bifrostcss-WnhIC').nth(0).click()
                page.wait_for_timeout(3000)

                page.click('text="vf-import-queue"')

                page.locator('text="Moving files to:"').wait_for(state="visible")
                # Cycle on each folder
                for folder in path.split("/"):
                    page.get_by_placeholder("Search").nth(1).fill(folder)
                    page.wait_for_timeout(3000)
                    page.locator(".bifrostcss-WnhIC").last.click()

                page.click('text="Move"')

        #click Run pipeline
        # Go to the page
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

        # Cleanup browser
        context.close()
        browser.close()


        return pipeline_filter
