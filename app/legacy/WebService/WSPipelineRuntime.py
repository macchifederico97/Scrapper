from playwright.sync_api import sync_playwright
from datetime import datetime

def scrape_pipeline_last_run(pipeline_filter: str, bifrost_instance: str, headlessPar:bool):
    """
    Scrapes the last pipeline execution filtered by name.
    Returns a dictionary with start time, finish time, and duration in minutes.
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
        page.locator(".bifrostcss-fFaJCf").nth(6).click()   # history
        page.wait_for_timeout(1000)
        
        if "/history" in page.url:
            print("URL corretto!")
        else:
            print("URL inatteso:", page.url)
            # Vai su una pipeline con /steps

            # Cambia URL a /history senza ricaricare
            page.evaluate("""
                const path = window.location.pathname;
                const base = path.substring(0, path.lastIndexOf('/'));
                const nuovaUrl = base + '/history';
                window.history.pushState({}, '', nuovaUrl);
            """)
            page.wait_for_timeout(2000)
        page.locator(".bifrostcss-bnFVuH").nth(0).click()   # last execution    #TODO GESTIRE QUANDO PIPELINE NON HA AVUTO DELLE RUN
        page.wait_for_timeout(500)

        # Extract start and finish times (as strings from the page)
        startTime = page.locator(".bifrostcss-bItxDa").nth(0).inner_text()
        finishTime = page.locator(".bifrostcss-bItxDa").nth(1).inner_text()
        page.wait_for_timeout(500)

        # Cleanup browser
        context.close()
        browser.close()

        # Try to compute duration in minutes
        duration_minutes = None
        try:
            dt_format = "%d/%m/%Y, %I:%M:%S %p %Z"
            start_dt = datetime.strptime(startTime, dt_format)
            finish_dt = datetime.strptime(finishTime, dt_format)
            duration_minutes = (finish_dt - start_dt).total_seconds() / 60.0
        except Exception as e:
            # If parsing fails, keep duration as None
            duration_minutes = None

        return {
            "pipeline_name": pipeline_filter,
            "start_time": startTime,
            "finish_time": finishTime,
            "duration_minutes": duration_minutes
        }

#scrape_pipeline_last_run("Claims - Reporting Update", "nttdata")