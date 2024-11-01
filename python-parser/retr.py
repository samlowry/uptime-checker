import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin


def parse_drupal_file_upload(main_url):
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
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
            
        form_id = form.get('id').split('-')[-1]
        print(f"Found form ID: {form_id}")

        # Find file upload field
        file_field = form.find('input', {'type': 'file'})
        if not file_field:
            print("File upload field not found")
            return None, None, None

        file_field_name = file_field.get('name')
        upload_button_name = file_field.find_next('input', {'type': 'submit'}).get('name')
        
        # Collect form data
        form_data = {
            'form_build_id': form.find('input', {'name': 'form_build_id'})['value'],
            'form_id': f'webform_client_form_{form_id}',
            'details[sid]': '',
            'details[page_num]': '1',
            'details[page_count]': '1',
            'details[finished]': '0',
            '_triggering_element_name': upload_button_name,
            '_triggering_element_value': 'Upload'
        }

        # Add file field
        files = {
            file_field_name: ('test.html', open('test.html', 'rb'), 'text/html')
        }

        # Find hidden fid field
        fid_field = form.find('input', {'name': lambda x: x and 'fid]' in x})
        if fid_field:
            form_data[fid_field['name']] = '0'

        print(f"\nFile field: {file_field_name}")
        print(f"Upload button: {upload_button_name}")
        
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


def pretty_print_json(data):
    """Print JSON in a human-readable format"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def post_form_upload(form_data, files, cookies, main_url):
    try:
        # Extract file field name from files dict
        file_field = list(files.keys())[0]  # e.g. 'files[submitted_adjunta_cv]'
        field_name = file_field[6:-1]  # e.g. submitted_adjunta_cv
        field_name = field_name.split('submitted_')[1]  # e.g. adjunta_cv
        
        # Construct correct AJAX URL
        base_url = main_url.split('/node')[0]
        ajax_url = f"{base_url}/file/ajax/submitted/{field_name}/{form_data['form_build_id']}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': main_url
        }

        print(f"\nSubmitting to AJAX endpoint:")
        print(f"URL: {ajax_url}")
        print("\nForm data:")
        pretty_print_json(form_data)
        print("\nFiles:", files)
        print("\nCookies:")
        pretty_print_json(cookies)

        response = requests.post(
            ajax_url,
            data=form_data,
            files=files,
            headers=headers,
            cookies=cookies
        )
        
        print("\nResponse Status:", response.status_code)
        print("\nResponse Headers:")
        pretty_print_json(dict(response.headers))
        
        try:
            json_response = response.json()
            print("\nJSON Response:")
            pretty_print_json(json_response)
            return response
        except ValueError:
            print("\nRaw Response:", response.text)
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


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
