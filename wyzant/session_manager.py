import requests
from google_cloud_secret_manager import access_secret
from bs4 import BeautifulSoup

def get_wyzant_session():
    # URL for the login page
    login_url = 'https://www.wyzant.com/login'

    # URL for the form submission
    post_login_url = 'https://www.wyzant.com/sso/login'

    # Start a session to persist cookies
    session = requests.Session()

    # Fetch the login page to get any hidden fields or tokens
    response = session.get(login_url)
    response.raise_for_status()  # Check if the request was successful

    # Extract the __RequestVerificationToken from the page
    soup = BeautifulSoup(response.content, 'html.parser')
    csrf_token_tag = soup.find('input', {'name': '__RequestVerificationToken'})
    request_verification_token = csrf_token_tag['value'] if csrf_token_tag else None

    if not request_verification_token:
        print("CSRF token couldn't be found")
    else:
        print("CSRF token found:", request_verification_token)

    USERNAME = access_secret('WYZANT_USER')
    PASSWORD = access_secret('WYZANT_PASSWORD')

    # Prepare the login payload
    payload = {
        'username': USERNAME,
        'password': PASSWORD
    }

    # Define headers including the __RequestVerificationToken
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        '__RequestVerificationToken': request_verification_token
    }

    # Send the login request with headers
    login_response = session.post(post_login_url, data=payload, headers=headers)
    login_response.raise_for_status()  # Check if the login request was successful

    # Check if login was successful, /tutor/jobs is locked behind login
    jobs_page = session.get('https://www.wyzant.com/tutor/jobs')
    response_soup = BeautifulSoup(jobs_page.text, 'html.parser')
    page_title = response_soup.title.string

    if page_title == 'Jobs | Wyzant Tutoring':
        print("Login successful")

    else:
        raise RuntimeError("Login unsuccessful")

    return session
