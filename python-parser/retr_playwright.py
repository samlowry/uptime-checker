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

        # Check for suspicious activity message
        body_text = await page.evaluate("document.body.innerText")
        if 'Suspicious activity detected' in body_text:
            print("Your IP address has been blocked. Please try again later.")
            await browser.close()
            return

        # Extract form ID, file field, auto-upload check, and submit button information
        form_data = await page.evaluate('''() => {
            const form = document.querySelector('form[id^="webform-client-form-"], form[id^="webform-submission"][id$="-form"]');
            if (!form) return { formId: null, fileFieldId: null, fileFieldName: null, autoUpload: false, submitButtonId: null, submitButtonName: null };

            const formId = form.id;

            // Find the file input and assign a unique ID if needed
            const fileField = form.querySelector('input[type="file"]');
            let fileFieldId = null;
            let fileFieldName = null;
            const autoUpload = fileField && fileField.getAttribute('data-once')?.includes('auto-');
            if (fileField) {
                if (!fileField.id) {
                    fileField.id = 'unique-file-input-' + Date.now();  // Generate a unique ID
                }
                fileFieldId = fileField.id;
                fileFieldName = fileField.name;
            }

            // Find the submit button and assign a unique ID if needed
            const submitButton = form.querySelector('input[type="submit"][value="Upload"], button[type="submit"][value="Upload"]');
            let submitButtonId = null;
            let submitButtonName = null;
            if (submitButton) {
                if (!submitButton.id) {
                    submitButton.id = 'unique-submit-button-' + Date.now();  // Generate a unique ID
                }
                submitButtonId = submitButton.id;
                submitButtonName = submitButton.name || 'Unnamed button';
            }

            return { formId, fileFieldId, fileFieldName, autoUpload, submitButtonId, submitButtonName };
        }''')

        # Extract the data returned from the evaluation
        form_id = form_data['formId']
        file_field_id = form_data['fileFieldId']
        file_field_name = form_data['fileFieldName']
        auto_upload = form_data['autoUpload']
        submit_button_id = form_data['submitButtonId']
        submit_button_name = form_data['submitButtonName']

        # Print extracted information for debugging and info purposes
        print(f"Form ID: {form_id}")
        print(f"File field ID: {file_field_id}")
        print(f"File field name: {file_field_name}")
        print(f"Auto-upload enabled: {auto_upload}")
        print(f"Submit button ID: {submit_button_id}")
        print(f"Submit button name: {submit_button_name}")

        # Step 2: Use the unique ID to interact with the file input and submit button

        # Upload file if file input is available
        file_name = 'test.html'  # Path to your file
        create_dummy_html(file_name)

        print(f"Uploading file: {file_name}")

        # Wait for the file input to be available and set the file using its unique ID
        try:
            await page.wait_for_selector(f'#{file_field_id}', timeout=10000)
            print(f"File input with ID '{file_field_id}' is available. Setting the file...")
            await page.set_input_files(f'#{file_field_id}', file_name)
            print("File has been set for upload.")
        except Exception as e:
            print(f"Error waiting for file input: {e}")
            await browser.close()
            return

        # Click the 'Upload' button if auto-upload is NOT enabled
        if not auto_upload:
            print("Submitting the form by clicking the 'Upload' button...")
            submit_button = await page.query_selector(f'#{submit_button_id}')
            if submit_button:
                await submit_button.click()
                print(f"Submit button with ID '{submit_button_id}' and name '{submit_button_name}' clicked.")
            else:
                print("Submit button not found.")
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
        os.remove(file_name)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python retr_playwright.py <URL>")
        sys.exit(1)

    main_url = sys.argv[1]
    asyncio.run(main(main_url))
