import requests
from bs4 import BeautifulSoup
import random
import json

# List of User-Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36',
    # Add more User-Agents as needed
]


def create_dummy_html():
    """Create a test HTML file"""
    content = """
    <!DOCTYPE html>
    <html><body><h1>Test File</h1></body></html>
    """
    with open("test.html", "w") as f:
        f.write(content)


def parse_drupal_file_upload(main_url, session=None):
    """Parse Drupal form and prepare file upload data"""
    try:
        session = session or requests.Session()

        # Select a random User-Agent
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }

        print("\nGetting form page...")
        response = session.get(main_url, headers=headers)

        # Check for suspicious activity message
        if '<h1>Suspicious activity detected' in response.text:
            print("Your IP address has been blocked. Please try again later.")
            return None, None, None, None

        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.select_one('form[id^="webform-client-form-"]')

        if not form:
            print("Form not found")
            return None, None, None, None

        form_id = form['id'].split('-')[-1]
        print(f"Found form ID: {form_id}")

        # Find file field
        file_field = form.find('input', {'type': 'file'})
        if not file_field:
            print("File field not found")
            return None, None, None, None

        file_field_name = file_field.get('name')
        upload_button = file_field.find_next('input', {'type': 'submit'})

        print(f"\nFile field: {file_field_name}")
        print(f"Upload button: {upload_button.get('name')}")

        # Prepare form data
        form_data = {
            'form_build_id': form.find('input', {'name': 'form_build_id'})['value'],
            'form_id': f'webform_client_form_{form_id}',
            'details[sid]': '',
            'details[page_num]': '1',
            'details[page_count]': '1',
            'details[finished]': '0',
            '_triggering_element_name': upload_button.get('name'),
            '_triggering_element_value': 'Upload'
        }

        # Add file field
        files = {file_field_name: ('test.html', open('test.html', 'rb'), 'text/html')}

        return form_data, files, session.cookies.get_dict(), session

    except Exception as e:
        print(f"Error: {e}")
        return None, None, None, None


def post_form_upload(form_data, files, cookies, main_url, session=None):
    try:
        session = session or requests.Session()
        if cookies:
            session.cookies.update(cookies)

        # Extract the base URL
        base_url = main_url.split('/webform')[0]

        # Construct the correct AJAX URL
        ajax_url = f"{base_url}/file/ajax/submitted/relevant_files/{form_data['form_build_id']}/{form_data['form_id']}"

        headers = {
            'User-Agent': random.choice(USER_AGENTS),
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

        response = session.post(
            ajax_url,
            data=form_data,
            files=files,
            headers=headers
        )

        print("\nResponse Status:", response.status_code)

        if response.ok:
            try:
                json_response = response.json()
                print("\nJSON Response:")
                pretty_print_json(json_response)
                return response
            except ValueError:
                print("\nRaw Response:", response.text)
                return None
        else:
            print("\nRequest failed")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def pretty_print_json(data):
    """Print JSON in a human-readable format"""
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py <URL>")
        sys.exit(1)

    main_url = sys.argv[1]
    create_dummy_html()
    form_data, files, cookies, session = parse_drupal_file_upload(main_url)

    if form_data and files:
        post_form_upload(form_data, files, cookies, main_url)
