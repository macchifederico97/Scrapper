from playwright.sync_api import sync_playwright

def instance_change(instance_description: str, page) -> str:
    """
    Change the instance to the instance passed as input, doesn't open the browser but works for a page already created
    """
    try:
        # Change the instance
        page.locator(".nav-css-jIaEVo").click()
        page.wait_for_timeout(1000)

        # 1. Hover over the menu trigger
        if page.locator("text = Switch Instance").count() == 0: #Handling when switch instance is not available for user
            return "Default instance is being used"
        page.hover("text = Switch Instance")
        page.wait_for_timeout(500)

        # 2. Click on the option with the text passed as parameter
        page.click(f"ul[role='listbox'] li[role='option']:has-text('{instance_description}')")
        page.wait_for_timeout(5000)

        # Cleanup browser

        return "Instance changed to: " + str(instance_description)
    except:
        return "Instance Change Error: Instance not changed. Using default instance"


#instance_change("Hain Daniels UK 3 QA")    #TEST & DEBUGGING
