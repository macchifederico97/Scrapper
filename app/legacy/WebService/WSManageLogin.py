from playwright.sync_api import sync_playwright
import os

def visualfabriq_login(organisation_id: str, mail: str, password: str) -> str:
    """
    Perform login to Visualfabriq and save the session state into 'state.json'.
    Returns a message describing the result.
    """

    HEADLESS = os.getenv("HEADLESS", "true").lower() == "false" #DEBUGGING, TO SET TO TRUE

    print("Starting login")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS  # headless=False = show the browser
            ,args=["--no-sandbox", "--ignore-certificate-errors"])
        if os.path.exists("state.json"):
            context = browser.new_context(storage_state="state.json")
        else:
            context = browser.new_context(device_scale_factor=1)
        page = context.new_page()
        page.goto("https://app.eu.visualfabriq.com/dashboard")
        page.wait_for_timeout(7000)

        # Handle the case where the user is not logged in
        if page.locator("#login-sso-organisation-id").count() != 0:
            print("User not logged in")
            # Perform login with the given parameters
            page.type("#login-sso-organisation-id", organisation_id)  # Insert Organisation ID
            page.wait_for_timeout(500)
            page.click("text=Continue")
            page.wait_for_timeout(7000)

            # If it asks for login after entering only Organisation ID
            if page.locator("#i0116").count() != 0:
                print("Logging in with mail and password")
                page.type("#i0116", mail)  # Insert email
                page.wait_for_timeout(500)

                page.click("#idSIButton9")
                page.type("#passwordInput", password)  # Insert password
                page.wait_for_timeout(500)
                page.click("#submitButton")
                page.click("#idSIButton9")
                page.wait_for_timeout(8000)  # Wait until the page is fully loaded

            # Save login state (cookies + localStorage) into a file
            page.context.storage_state(path="state.json")
            browser.close()
            print("User logged in")
            return "Login file 'state.json' created correctly"
        else:
            browser.close()
            return "User already logged in"

print(visualfabriq_login("nttdata","",""))