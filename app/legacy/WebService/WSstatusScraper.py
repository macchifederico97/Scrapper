from playwright.sync_api import sync_playwright, TimeoutError
import json


# ----------------------------
# Main scraping function for API
# ----------------------------
def scrape_pipeline_status(bifrost_instance: str, filter_enabled: bool, headlessPar: bool):
    """
    Scrapes Bifrost pipelines and returns their last run status.
    Parameters:
        filter_enabled (bool): whether to filter for pipelines with status 'Enabled'
    Returns:
        dict: {pipeline_name: last_run_status}
    """

    outputList = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headlessPar,  # Use headless for webservice/API
        args=["--no-sandbox", "--ignore-certificate-errors"]
            #,executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        )
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        # GET PIPELINE ID
        with open(f"client/{bifrost_instance}/pipeline.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        # Go to the page
        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")
        page.wait_for_timeout(20000)
        page.wait_for_load_state()

        pipeline_status_dict = {}   #CREO IL DICT DOVE SALVARE LE INFO DELLA PIPELINE
        checkpipelineNames = []  #FUNCTION OUTPUT CHECK LIST
        exit_loop = False
        
        element_list=[]
        for item in data["pipelines"]:
                if(str(filter_enabled).lower() == "true"):
                    if(item["status"] == "Enabled"):
                        element_list.append(item["pipeline_name"])
                else:
                    element_list.append(item["pipeline_name"])

        while not exit_loop:
            elements_name = page.locator(".bifrostcss-eXwpzm")
            elements_history = page.locator(".bifrostcss-hDzPRB")

            count = elements_name.count()
            if count == 0:
                break
            
            first_pipeline_name = elements_name.nth(0).inner_text()
            print(first_pipeline_name)
            if first_pipeline_name in checkpipelineNames:
                break  # Already visited this page

            for i in range(count):  #TO CHECK, FASTER
                pipeline_status_dict = {}
                print("---------")
                element_name = elements_name.nth(i).inner_text()
                print(element_name)
                if(element_name in element_list):
                    element_history = elements_history.nth(i).locator("svg").nth(0).get_attribute("class")
                    #Green
                    if(element_history == "bifrostcss-dSdRKl"): 
                        pipeline_status_dict["pipeline_name"] = element_name
                        pipeline_status_dict["status"] = "Successful"
                    #Blue
                    else:
                        if(element_history == "bifrostcss-fuPzxl"):
                            pipeline_status_dict["pipeline_name"] = element_name
                            pipeline_status_dict["status"] = "No Action"
                    #Red
                        else: 
                            if(element_history == "bifrostcss-hBAxAh"):
                                path = elements_history.nth(i).locator("svg").nth(0).locator("path").nth(0).get_attribute("d")
                                #!
                                if(path.startswith("M12.257")):
                                    pipeline_status_dict["pipeline_name"] = element_name
                                    pipeline_status_dict["status"] = "Failed"
                                #X
                                if(path.startswith("M12.7523")):
                                    pipeline_status_dict["pipeline_name"] = element_name
                                    pipeline_status_dict["status"] = "Stopped"
                            else: 
                                pipeline_status_dict["pipeline_name"] = element_name
                                pipeline_status_dict["status"] = "Never Execute"

                    print(pipeline_status_dict["status"])
                    checkpipelineNames.append(element_name)
                    outputList.append(pipeline_status_dict)

            # Go to next page
            page.click("text=Next")
            page.wait_for_load_state()
            page.wait_for_timeout(2000)

    return outputList

#print(scrape_pipeline_status("nttdata", False, False))    #DEBUGGING & TEST