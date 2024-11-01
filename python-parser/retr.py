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

        # Find form with file upload
        upload_form = soup.find('form', enctype='multipart/form-data')
        if not upload_form:
            print("No upload form found")
            return None, None, None

        # Get form action URL
        form_url = urljoin(main_url, upload_form.get('action', main_url))
        print(f"\nForm URL: {form_url}")

        # Collect all form fields
        form_data = {}
        for input_field in upload_form.find_all(['input', 'select', 'textarea']):
            if input_field.get('type') != 'file':
                name = input_field.get('name')
                if name:
                    form_data[name] = input_field.get('value', '')
                    print(f"Found field: {name}")

        return form_url, form_data, session.cookies.get_dict()

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


def post_form_upload(form_url, form_data, cookies=None, main_url=None):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': main_url,
            'Connection': 'keep-alive'
        }

        # Debug output
        print("\nSubmitting form:")
        print(f"URL: {form_url}")
        print("\nForm data:")
        for k, v in form_data.items():
            print(f"{k}: {v}")
        print("\nCookies:", cookies)

        files = {'file': ('test.html', open('test.html', 'rb'), 'text/html')}
        
        response = requests.post(
            form_url,
            data=form_data,
            files=files,
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
        form_url, form_data, cookies = parse_drupal_file_upload(main_url)
        create_dummy_html()
        if form_url and form_data:
            post_form_upload(form_url, form_data, cookies, main_url)
