import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin


def parse_drupal_file_upload(main_url):
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate'
        }

        print("\nGetting form page...")
        response = session.get(main_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find form with dynamic ID
        form = soup.find('form', id=lambda x: x and x.startswith('webform-client-form-'))
        if not form:
            print("Form not found")
            return None, None, None
            
        # Get form ID number for later use
        form_id = form.get('id').split('-')[-1]
        print(f"Found form ID: {form_id}")
        
        # Collect form data
        form_data = {
            'submitted[name]': 'Test Name',
            'submitted[email]': 'test@example.com',
            'submitted[please_upload_your_cv][fid]': '0',
            'details[sid]': '',
            'details[page_num]': '1',
            'details[page_count]': '1',
            'details[finished]': '0',
            'form_build_id': form.find('input', {'name': 'form_build_id'})['value'],
            'form_id': f'webform_client_form_{form_id}',  # Use dynamic form ID
            '_triggering_element_name': 'submitted_please_upload_your_cv_upload_button',
            '_triggering_element_value': 'Upload'
        }

        # Add file field
        files = {
            'files[submitted_please_upload_your_cv]': ('test.html', open('test.html', 'rb'), 'text/html')
        }

        return form_data, files, session.cookies.get_dict()

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


def post_form_upload(form_data, files, cookies=None, main_url=None):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': main_url.split('/node')[0],
            'Referer': main_url
        }

        # Get AJAX URL from form action
        ajax_url = f"{main_url.split('/node')[0]}/file/ajax/submitted/please_upload_your_cv/{form_data['form_build_id']}"

        print("\nSubmitting to AJAX endpoint:")
        print(f"URL: {ajax_url}")
        print("\nForm data:", form_data)
        print("\nFiles:", files)
        print("\nCookies:", cookies)

        response = requests.post(
            ajax_url,
            data=form_data,
            files=files,
            headers=headers,
            cookies=cookies
        )
        
        print("\nResponse Status:", response.status_code)
        print("Response Headers:", dict(response.headers))
        
        try:
            json_response = response.json()
            print("\nJSON Response:", json_response)
        except ValueError:
            print("\nRaw Response:", response.text)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py <URL>")
        create_dummy_html()
    else:
        main_url = sys.argv[1]
        form_data, files, cookies = parse_drupal_file_upload(main_url)
        create_dummy_html()
        if form_data and files:
            post_form_upload(form_data, files, cookies, main_url)
