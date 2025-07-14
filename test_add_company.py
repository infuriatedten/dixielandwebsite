import requests
import re

# Login
login_url = "http://localhost:5001/auth/login"
session = requests.Session()
response = session.get(login_url)
csrf_token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', response.text).group(1)

login_data = {
    "username": "testuser",
    "password": "password",
    "csrf_token": csrf_token
}

response = session.post(login_url, data=login_data, allow_redirects=True)

# Add Company
profile_url = "http://localhost:5001/auth/profile"
response = session.get(profile_url)
csrf_token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', response.text).group(1)

company_data = {
    "name": "Test Company",
    "details": "This is a test company.",
    "csrf_token": csrf_token
}

response = session.post(profile_url, data=company_data, allow_redirects=True)

print(response.text)
