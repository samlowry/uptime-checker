from flask import Flask, request, jsonify
import os
import random
import aiohttp
from playwright.async_api import async_playwright

app = Flask(__name__)

# List of User-Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36',
    # Add more User-Agents as needed
]


async def download_file(file_url, file_name):
    """Download a file from a URL"""
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as response:
            if response.status == 200:
                with open(file_name, 'wb') as f:
                    f.write(await response.read())
            else:
                raise Exception(f"Failed to download file: {response.status}")


async def main(url, file_name):
    async with async_playwright() as p:
        # Launch the browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
        page = await context.new_page()

        print("Getting form page...")
        await page.goto(url)

        # Wait for the page to fully load
        await page.wait_for_load_state("load")

        print("Page fully loaded, starting operations...")

        # Check for suspicious activity message
        body_text = await page.evaluate("document.body.innerText")
        if 'Suspicious activity detected' in body_text:
            print("Your IP address has been blocked. Please try again later.")
            await browser.close()
            return

        # Locate the file input element
        file_input = await page.query_selector('input[type="file"]:nth-of-type(1)')  # Change as needed

        if file_input:
            print(f"Uploading file: {file_name}")
            await file_input.set_input_files(file_name)
            print("File has been set for upload.")
        else:
            print("File input not found.")

        # Additional logic for submitting the form and handling responses...

        await browser.close()
        os.remove(file_name)


@app.route('/upload', methods=['POST'])
async def upload_file():
    data = request.json
    url = data.get('url')
    file_url = data.get('file_url')

    if not url or not file_url:
        return jsonify({"error": "URL and file_url are required."}), 400

    file_name = os.path.basename(file_url)  # Extract the original file name from the URL

    try:
        await download_file(file_url, file_name)  # Download the file
        await main(url, file_name)  # Call your main function with the provided URL and file name
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "File uploaded successfully."}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
