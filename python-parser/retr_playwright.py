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


async def main(url):
    async with async_playwright() as p:
        # Launch the browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
        page = await context.new_page()

        print("Getting form page...")
        await page.goto(url)

        # Check for suspicious activity message
        body_text = await page.evaluate("document.body.innerText")
        if 'Suspicious activity detected' in body_text:
            print("Your IP address has been blocked. Please try again later.")
            await browser.close()
            return

        # Use a wildcard selector to find the form and then locate the file input within it
        file_field_name = await page.evaluate('''() => {
            const form = document.querySelector('form[id^="webform-client-form-"]');
            const fileField = form ? form.querySelector('input[type="file"]') : null;
            return fileField ? fileField.name : null;
        }''')

        print(f"File field: {file_field_name}")

        # Upload file
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

        # Submit the form
        print("Submitting the form...")
        await page.click('input[type="submit"]')

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
    asyncio.run(main(main_url))
