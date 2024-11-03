import asyncio
from playwright.async_api import async_playwright
import random
import os

# List of User-Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36',
    # Add more User-Agents as needed
]


def create_dummy_html(file_name):
    """Create a test HTML file"""
    content = """
    <!DOCTYPE html>
    <html><body><h1>Tost ^^^ File</h1></body></html>
    """
    with open(file_name, "w") as f:
        f.write(content)


async def main(url):
    async with async_playwright() as p:
        # Launch the browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
        page = await context.new_page()

        # Intercept network requests to log AJAX submissions
        async def log_request(route):
            request = route.request
            print(f"Request URL: {request.url}")
            print(f"Request Method: {request.method}")
            print(f"Request Post Data: {request.post_data}")
            await route.continue_()

        page.on("route", log_request)

        print("Getting form page...")
        await page.goto(url)

        # Wait for the page to fully load
        await page.wait_for_load_state("load")  # Waits until the 'load' event is fired

        print("Page fully loaded, starting operations...")

        # Check for suspicious activity message
        body_text = await page.evaluate("document.body.innerText")
        if 'Suspicious activity detected' in body_text:
            print("Your IP address has been blocked. Please try again later.")
            await browser.close()
            return

        # Step 1: File Input

        # 1. Locate the file input element
        file_input = await page.query_selector('input[type="file"]')

        # 2. Extract and print name and auto-upload status if file input is found
        if file_input:
            file_input_data = await page.evaluate('''fileInput => {
                return {
                    fileFieldName: fileInput.name,
                    autoUpload: fileInput.getAttribute("data-once")?.includes("auto-") || false
                };
            }''', file_input)

            # Print file input details directly
            print(f"File input name: {file_input_data['fileFieldName']}")
            print(f"Auto-upload enabled: {file_input_data['autoUpload']}")

            # 3. Set the file
            file_name = 'test.html'  # Path to your file
            create_dummy_html(file_name)
            print(f"Uploading file: {file_name}")

            await file_input.set_input_files(file_name)
            print("File has been set for upload.")
        else:
            print("File input not found.")

        # Step 2: Submit Button (if Auto-Upload is Disabled)

        # Only proceed to click the submit button if auto-upload is disabled
        if not file_input_data['autoUpload']:
            try:
                # Wait for the submit button to be attached to the DOM
                await page.wait_for_selector('input[type="submit"][value="Upload"], button[type="submit"][value="Upload"]', state="attached", timeout=5000)
                submit_button = await page.query_selector('input[type="submit"][value="Upload"], button[type="submit"][value="Upload"]')
                if submit_button:
                    submit_button_name = await page.evaluate('button => button.name || "Unnamed button"', submit_button)
                    print(f"Submit button name: {submit_button_name}")
                    await submit_button.click()
                    print(f"Submit button with name '{submit_button_name}' clicked.")
                else:
                    print("Submit button not found. Assuming auto-upload is enabled, no need to click the 'Upload' button.")
            except Exception as e:
                print("Submit button is not attached or visible:", e)
        else:
            print("Auto-upload is enabled, no need to click the 'Upload' button.")

        # Step 3: Wait for the new file link to appear
        try:
            print("Waiting for the file link to appear...")
            await page.wait_for_selector('span.file a', timeout=10000)  # Wait for the file link to appear
            print("File uploaded successfully.")
        except Exception as e:
            print("File upload did not complete successfully:", e)
            await browser.close()
            return

        # Extract the file path and name
        file_link = await page.evaluate('''() => {
            const fileElement = document.querySelector('span.file a');
            return fileElement ? {
                href: fileElement.href,
                text: fileElement.innerText
            } : null;
        }''')

        if file_link:
            print(f"Uploaded file link: {file_link['href']}")
            print(f"Uploaded file name: {file_link['text']}")
        else:
            print("Uploaded file link not found.")

        await browser.close()
        os.remove(file_name)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python retr_playwright.py <URL>")
        sys.exit(1)

    main_url = sys.argv[1]
    asyncio.run(main(main_url))
