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
