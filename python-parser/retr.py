import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin


def parse_drupal_file_upload(main_url):
    try:
        # Initial browser-like session
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }

        # Get page with form
        print("\nGetting form page...")
        response = session.get(main_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find file upload input
        file_input = soup.find('input', type='file')
        if not file_input:
            print("No file input found")
            return None, None, None

        # Get AJAX URL from the file input's parent form
        ajax_url = urljoin(main_url, '/system/ajax')  # Drupal's AJAX endpoint
        
        # Get form data for the AJAX request
        form_data = {
            'files[submitted_please_upload_your_cv]': ('test.html', open('test.html', 'rb'), 'text/html'),
            'form_build_id': soup.find('input', {'name': 'form_build_id'})['value']
        }

        return ajax_url, form_data, session.cookies.get_dict()

    except Exception as e:
        print(f"Error: {e}")
        return None, None, None


def create_dummy_html():
    dummy_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dummy Test</title>
    </head>
    <body>
        <h1>This is a Dummy Test HTML File</h1>
        <p>Short content for testing purposes.</p>
    </body>
    </html>
    """
    with open("test.html", "w") as file:
        file.write(dummy_content)
    print("Dummy HTML file 'test.html' created successfully.")


def post_form_upload(ajax_url, form_data, cookies=None, main_url=None):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': main_url,
            'Connection': 'keep-alive'
        }

        # Debug output
        print("\nSubmitting to AJAX endpoint:")
        print(f"URL: {ajax_url}")
        print("\nForm data:", form_data)
        print("\nCookies:", cookies)

        response = requests.post(
            ajax_url,
            files=form_data,
            headers=headers,
            cookies=cookies
        )
        response.raise_for_status()
        
        print("\nResponse:")
        try:
            json_response = response.json()
            for command in json_response:
                if command['command'] == 'insert':
                    soup = BeautifulSoup(command['data'], 'html.parser')
                    print(f"\nAlert: {soup.get_text().strip()}")
                elif command['command'] == 'settings':
                    print(f"\nSettings: Base Path: {command['settings']['basePath']}")
        except ValueError:
            print(response.text)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py <URL>")
        create_dummy_html()
    else:
        main_url = sys.argv[1]
        ajax_url, form_data, cookies = parse_drupal_file_upload(main_url)
        create_dummy_html()
        if ajax_url and form_data:
            post_form_upload(ajax_url, form_data, cookies, main_url)
