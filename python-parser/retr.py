import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin


def parse_drupal_file_upload(main_url):
    try:
        # Get initial cookies
        session = requests.Session()
        response = session.get(main_url)
        response.raise_for_status()
        html_content = response.text
        cookies = session.cookies.get_dict()

        # Step 2: Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Step 3: Find div with id ending in 'ajax-wrapper'
        ajax_wrappers = soup.find_all('div', id=re.compile(r'edit-submitted-.*-ajax-wrapper'))
        if not ajax_wrappers:
            print("Error: Could not find any AJAX wrapper divs.")
            return None, None

        for wrapper in ajax_wrappers:
            form_item = wrapper.find('div', class_='form-item')
            if form_item:
                label = form_item.find('label')
                input_file = form_item.find('input', {'type': 'file'})
                if label and input_file:
                    print(f"Found File Upload: {label.text.strip()}")
                    print(f"Input ID: {input_file.get('id')}, Name: {input_file.get('name')}")

        # Step 4: Extract the Drupal settings script
        script_tag = soup.find('script', string=re.compile(r'Drupal\.settings'))
        if not script_tag:
            print("Error: Could not find Drupal settings in script tags.")
            return None, None

        # Extract JSON data from the Drupal.settings script
        script_content = script_tag.string
        drupal_settings_match = re.search(r'Drupal\.settings, (\{.*\})\);', script_content)
        if not drupal_settings_match:
            print("Error: Could not parse Drupal settings JSON.")
            return None, None

        drupal_settings_json = drupal_settings_match.group(1)
        drupal_settings = json.loads(drupal_settings_json)

        # Step 5: Extract file upload configuration from the JSON
        ajax_settings = drupal_settings.get('ajax', {})
        file_elements = drupal_settings.get('file', {}).get('elements', {})

        ajax_endpoint = None
        for key, value in ajax_settings.items():
            if 'upload' in key.lower():
                ajax_endpoint = value.get('url', None)
                if ajax_endpoint:
                    ajax_endpoint = urljoin(main_url, ajax_endpoint)  # Convert to absolute URL
                    print(f"Found AJAX Upload Endpoint: {ajax_endpoint}")
                    break

        for element, allowed_types in file_elements.items():
            print(f"File Input Element: {element}, Allowed Types: {allowed_types}")

        return ajax_endpoint, cookies

    except requests.exceptions.RequestException as e:
        print(f"Error occurred while making a request: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

    return None, None


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


def post_dummy_html(ajax_endpoint, main_url=None, cookies=None):
    if not ajax_endpoint:
        print("No valid AJAX endpoint provided. Skipping file upload.")
        return
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': main_url
        }
        files = {'file': ('test.html', open('test.html', 'rb'), 'text/html')}
        
        # Debug output
        print("\nPOST Request Details:")
        print(f"URL: {ajax_endpoint}")
        print("\nHeaders:")
        for k, v in headers.items():
            print(f"{k}: {v}")
        print("\nCookies:")
        print(cookies)
        print("\nFiles:")
        print(f"Filename: test.html")
        print(f"Content-Type: text/html")
        print("-------------------")
        
        response = requests.post(ajax_endpoint, files=files, headers=headers, cookies=cookies)
        response.raise_for_status()
        print("Dummy HTML file posted successfully.")
        print("\nResponse from server:")
        
        json_response = response.json()
        for command in json_response:
            if command['command'] == 'insert':
                soup = BeautifulSoup(command['data'], 'html.parser')
                print(f"\nAlert: {soup.get_text().strip()}")
            elif command['command'] == 'settings':
                print(f"\nSettings: Base Path: {command['settings']['basePath']}")
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while posting the dummy HTML file: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py <URL>")
        create_dummy_html()
    else:
        main_url = sys.argv[1]
        ajax_endpoint, cookies = parse_drupal_file_upload(main_url)
        create_dummy_html()
        post_dummy_html(ajax_endpoint, main_url, cookies)
