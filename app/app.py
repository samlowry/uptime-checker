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
            return None, None  # Return None for both values

        # Step 1: File Input
        file_input = await page.query_selector('input[type="file"]:not([accept*="image"])')

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
            print(f"Uploading file: {file_name}")
            await file_input.set_input_files(file_name)
            print("File has been set for upload.")
        else:
            print("File input not found.")

        # Step 2: Submit Button (if Auto-Upload is Disabled)
        if not file_input_data['autoUpload']:
            try:
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
            return None, None  # Return None for both values

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
            await browser.close()
            return file_link['href'], os.path.basename(file_link['href'])  # Return the URL and name extracted from the URL
        else:
            print("Uploaded file link not found.")
            await browser.close()
            return None, None  # Return None for both values

@app.route('/upload', methods=['POST'])
async def upload_file():
    data = request.json
    url = data.get('url')
    file_url = data.get('file_url')

    if not url or not file_url:
        return jsonify({"error": "URL and file_url are required."}), 400

    # Extract the original file name from the URL
    file_name = os.path.basename(file_url)

    try:
        await download_file(file_url, file_name)  # Download the file
        uploaded_file_url, uploaded_file_name = await main(url, file_name)  # Call your main function with the provided URL and file name
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Delete the temporary file after processing
        if os.path.exists(file_name):
            os.remove(file_name)

    if uploaded_file_url and uploaded_file_name:
        return jsonify({
            "message": "File uploaded successfully.",
            "uploaded_file_url": uploaded_file_url,
            "uploaded_file_name": uploaded_file_name  # This is now extracted from the uploaded file URL
        }), 200
    else:
        return jsonify({"error": "File upload failed."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
