from playwright.sync_api import sync_playwright

# ----------------------------
# Helper Functions
# ----------------------------
def _get_status_box_pos_x(page, valid_classes):
    """
    Returns the X coordinate of the first valid status box on the page.
    Returns 0 if no boxes are found.
    """
    x_positions = []
    for bifrost_class in valid_classes:
        elements = page.locator(bifrost_class)
        count = elements.count()
        if count != 0:
            element = elements.nth(0)
            box = element.bounding_box()
            center_x = box["x"] + (box["width"] / 2)
            x_positions.append(center_x)

    return min(x_positions) if x_positions else 0


def _get_status_box_pos_y(box):
    """
    Given a box, returns its center Y coordinate.
    """
    return box["y"] + box["height"] / 2


def _get_status_text(page, pos_x, pos_y):
    """
    Moves the mouse to a pipeline status position, double-clicks to highlight text,
    and returns the selected text as the status of the last run.
    """
    page.mouse.move(pos_x, pos_y)
    page.wait_for_timeout(500)
    page.mouse.dblclick(pos_x, pos_y - 43)  # Offset for hover text
    return page.evaluate("window.getSelection().toString()").strip()


def _filter_status_enabled(page):
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


# ----------------------------
# Main scraping function for API
# ----------------------------
def scrape_pipeline_status(bifrost_instance: str, filter_enabled: str, headlessPar: bool):
    """
    Scrapes Bifrost pipelines and returns their last run status.
    Parameters:
        filter_enabled (bool): whether to filter for pipelines with status 'Enabled'
    Returns:
        dict: {pipeline_name: last_run_status}
    """
    valid_bifrost_classes = [".bifrostcss-hBAxAh", ".bifrostcss-dSdRKl", ".bifrostcss-fuPzxl"]
    valid_statuses = ["Successful", "Failed", "Stopped", "No Action"]

    pipeline_status_dict = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headlessPar,  # Use headless for webservice/API
        args=["--no-sandbox", "--ignore-certificate-errors"])
        context = browser.new_context(storage_state="state.json", device_scale_factor=1)
        page = context.new_page()
        page.set_viewport_size({"width": 1600, "height": 1200})

        page.goto(f"https://app.eu.visualfabriq.com/bifrost/{bifrost_instance}/pipelines")

        page.wait_for_load_state()
        page.wait_for_timeout(8000)

        filterEnabled = filter_enabled.lower()
        if filterEnabled == "true":
            _filter_status_enabled(page)

        exit_loop = False
        while not exit_loop:
            elements = page.locator(".bifrostcss-eXwpzm.undefined")
            count = elements.count()

            if count == 0:
                break

            first_pipeline_name = elements.nth(0).inner_text()
            if first_pipeline_name in pipeline_status_dict:
                break  # Already visited this page

            status_pos_x = _get_status_box_pos_x(page, valid_bifrost_classes)
            if status_pos_x == 0:
                continue  # Skip if no status boxes

            for i in range(count):
                element = elements.nth(i)
                pipeline_name = element.inner_text()
                box = element.bounding_box()

                if status_pos_x == 0:
                    status_text = "Never Executed"
                else:
                    status_pos_y = _get_status_box_pos_y(box)
                    status_text = _get_status_text(page, status_pos_x, status_pos_y)

                if status_text == "Action":
                    status_text = "No Action"
                if status_text not in valid_statuses:
                    status_text = "Never Executed"

                pipeline_status_dict[pipeline_name] = status_text
                
            

            # Go to next page
            page.click("text=Next")
            page.wait_for_load_state()
            page.wait_for_timeout(2000)

        browser.close()
        
        converted = [
                {"pipeline_name": pipeline_name, "status": status_text}
                for pipeline_name, status_text in pipeline_status_dict.items()
            ]
    return converted