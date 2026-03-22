import requests
import time

BASE_URL = "http://localhost:8000"

def test_routes():
    # Login as admin
    session = requests.Session()
    # Need CSRF token
    login_page = session.get(f"{BASE_URL}/auth/login")
    csrf_token = ""
    for line in login_page.text.split('\n'):
        if 'name="csrf_token"' in line:
            csrf_token = line.split('value="')[1].split('"')[0]
            break

    login_resp = session.post(f"{BASE_URL}/auth/login", data={
        "username": "admin",
        "password": "AdminPassword123!",
        "csrf_token": csrf_token
    }, allow_redirects=True)
    print(f"Login status: {login_resp.status_code}")
    print(f"Logged in as: {login_resp.url}")

    # Check Admin Add Parcel page
    resp = session.get(f"{BASE_URL}/admin/add_parcel")
    if resp.status_code == 200:
        print("PASS: /admin/add_parcel is accessible")
    else:
        print(f"FAIL: /admin/add_parcel returned {resp.status_code}")
        # print(resp.text)

    # Check timesheet routes (should be 404 since blueprint is disabled)
    resp = session.post(f"{BASE_URL}/timesheet/clock_in")
    if resp.status_code == 404:
        print("PASS: /timesheet/clock_in is disabled (404)")
    else:
        print(f"FAIL: /timesheet/clock_in returned {resp.status_code}")

    # Check Discord links on homepage
    resp = requests.get(f"{BASE_URL}/")
    if "https://discord.gg/kfDtPS9dcm" in resp.text:
        print("PASS: New Discord link found on homepage")
    else:
        print("FAIL: New Discord link NOT found on homepage")

if __name__ == "__main__":
    test_routes()
