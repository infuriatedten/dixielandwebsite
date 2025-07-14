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

# Register as a farmer
profile_url = "http://localhost:5001/auth/profile"
response = session.get(profile_url)
csrf_token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', response.text).group(1)

farmer_data = {
    "csrf_token": csrf_token,
    "submit": "Register as Farmer"
}

response = session.post(profile_url, data=farmer_data, allow_redirects=True)

# Add a parcel
response = session.get(profile_url)
csrf_token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', response.text).group(1)

parcel_data = {
    "location": "Test Location",
    "size": 10.5,
    "csrf_token": csrf_token,
    "submit": "Add Parcel"
}

response = session.post(profile_url, data=parcel_data, allow_redirects=True)

print(response.text)
