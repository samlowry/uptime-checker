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


def create_dummy_html():
    """Create a test HTML file"""
    content = """
    <!DOCTYPE html>
    <html><body><h1>Test File</h1></body></html>
    """
    with open("test.html", "w") as f:
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

        # Check for suspicious activity message
        body_text = await page.evaluate("document.body.innerText")
        if 'Suspicious activity detected' in body_text:
            print("Your IP address has been blocked. Please try again later.")
            await browser.close()
            return

        # Extract form ID, file field, and check if auto-upload is enabled
        form_data = await page.evaluate('''() => {
            const form = document.querySelector('form[id^="webform-client-form-"], form[id^="webform-submission"][id$="-form"]');
            if (!form) return { formId: null, fileFieldName: null, autoUpload: false };

            const formId = form.id;
            const fileField = form.querySelector('input[type="file"]');
            const fileFieldName = fileField ? fileField.name : null;
            const autoUpload = fileField && fileField.getAttribute('data-once')?.includes('auto-');

            return { formId, fileFieldName, autoUpload };
        }''')

        form_id = form_data['formId']
        file_field_name = form_data['fileFieldName']
        auto_upload = form_data['autoUpload']

        print(f"Found form ID: {form_id}")
        print(f"File field name: {file_field_name}")
        print(f"Auto-upload enabled: {auto_upload}")

        # Upload file if file input is available
        file_path = 'test.html'  # Path to your file
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            await browser.close()
            return

        print(f"Uploading file: {file_path}")

        # Wait for the file input to be available
        try:
            await page.wait_for_selector(f'input[name="{file_field_name}"]', timeout=10000)
            print("File input is available. Setting the file...")
            await page.set_input_files(f'input[name="{file_field_name}"]', file_path)
            print("File has been set for upload.")
        except Exception as e:
            print(f"Error waiting for file input: {e}")
            await browser.close()
            return

        # Click the 'Upload' button if auto-upload is NOT enabled
        if not auto_upload:
            print("Submitting the form by clicking the 'Upload' button...")
            upload_button_info = await page.evaluate('''() => {
                const button = document.querySelector('input[type="submit"][value="Upload"]');
                if (button) {
                    button.click();
                    return button.name || 'Unnamed button';
                }
                return null;
            }''')

            if upload_button_info:
                print(f"Upload button clicked. Button name: {upload_button_info}")
            else:
                print("Upload button not found.")

        else:
            print("Auto-upload is enabled, no need to click the 'Upload' button.")

        # Wait for the new file link to appear
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

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python retr_playwright.py <URL>")
        sys.exit(1)

    main_url = sys.argv[1]
    create_dummy_html()
    asyncio.run(main(main_url))
