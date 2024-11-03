import asyncio
from playwright.async_api import async_playwright
import random
import os
import sys

# List of User-Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36',
]


async def main(url):
    async with async_playwright() as p:
        # Launch browser with a random User-Agent
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
        page = await context.new_page()

        # Intercept network requests to log AJAX submissions
        page.on("route", lambda route: print(f"Request: {route.request.url}, Method: {route.request.method}, Data: {route.request.post_data}") or route.continue_())

        print("Navigating to the form page...")
        await page.goto(url)

        # Check if access is blocked
        if 'Suspicious activity detected' in await page.inner_text("body"):
            print("Access blocked. Please try again later.")
            await browser.close()
            return

        # Locate file input within the form
        file_field_name = await page.evaluate('''() => {
            const form = document.querySelector('form[id^="webform-client-form-"]');
            const fileField = form?.querySelector('input[type="file"]');
            return fileField?.name || null;
        }''')

        if not file_field_name:
            print("File input not found.")
            await browser.close()
            return

        print(f"File field name: {file_field_name}")

        # Verify file path
        file_path = 'test.html'
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            await browser.close()
            return

        print(f"Uploading file: {file_path}")

        # Upload file
        await page.set_input_files(f'input[name="{file_field_name}"]', file_path)
        print("File uploaded successfully.")

        # Submit form
        await page.click('input[type="submit"]')
        print("Form submitted. Waiting for file link...")

        # Wait for and extract uploaded file link
        file_link = await page.evaluate('''() => {
            const link = document.querySelector('span.file a');
            return link ? { href: link.href, text: link.innerText } : null;
        }''')

        if file_link:
            print(f"Uploaded file link: {file_link['href']}")
            print(f"Uploaded file name: {file_link['text']}")
        else:
            print("No file link found.")

        await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python retr_playwright.py <URL>")
        sys.exit(1)

    asyncio.run(main(sys.argv[1]))
