from playwright.sync_api import sync_playwright
from InstanceChange import instance_change


def scrape_user_list(visualfabriq_instance: str, headlessPar: bool):
    """
    Scrape the Visualfabriq user list

    Returns:
        dict: Information about the captured API response.
    """

    def _handle_response(response):
        """Private listener to capture the specific API response."""
        print("Checking response URL:", response.url)  # Debugging line
        if response.url.endswith("/api/user/list"):
            try:
                print("aaaaaaaaaaaaaa")
                return {
                    "url": response.url,
                    "status": response.status,
                    "body": response.json(),  # Parse JSON directly
                }
            except Exception as e:
                return {
                    "url": response.url,
                    "status": response.status,
                    "error": str(e),
                }
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headlessPar,  #Not showing the browser window
        args=["--no-sandbox", "--ignore-certificate-errors"])
        context = browser.new_context(
            storage_state="state.json",
            device_scale_factor=1,
            ignore_https_errors =True
        )
        page = context.new_page()
        page.goto("https://app.eu.visualfabriq.com/Dashboard")
        if (visualfabriq_instance != ""):   #Change instance if
            print(instance_change(visualfabriq_instance, page)) #Visualfabriq instance change
        else: print("Default instance is being used")

        # Placeholder for response data
        captured_response = {"status": "not found"}

        # Attach listener
        def response_listener(response):
            nonlocal captured_response
            result = _handle_response(response)
            if result:
                captured_response = result

        page.on("response", response_listener)

        # Navigate to trigger requests
        page.goto("https://app.eu.visualfabriq.com/configuration/user-and-access/user")
        page.wait_for_timeout(5000)  # Wait for background requests

        vf_instance = page.locator(".nav-css-fCKCJV").text_content()    #Returning also the visualfabriq_instance used for the export

        browser.close()

        return captured_response, vf_instance

#print(scrape_user_list("Hain Daniels UK 3 QA"))     #TEST & DEBUGGING