import requests
import sys

BASE_URL = "http://localhost:8000"

def reproduce():
    session = requests.Session()
    # Need CSRF token
    try:
        login_page = session.get(f"{BASE_URL}/auth/login")
        csrf_token = ""
        for line in login_page.text.split('\n'):
            if 'name="csrf_token"' in line:
                csrf_token = line.split('value="')[1].split('"')[0]
                break

        login_resp = session.post(f"{BASE_URL}/auth/login", data={
            "username": "farmer1",
            "password": "password",
            "csrf_token": csrf_token
        }, allow_redirects=True)

        print(f"Login URL: {login_resp.url}")

        resp = session.get(f"{BASE_URL}/")
        print(f"Home Page Status: {resp.status_code}")

        if resp.status_code == 500:
            print("ERROR 500 detected!")
            return False

        if "UndefinedError" in resp.text or "parcel_form" in resp.text:
            print("Found issue in response text")
            # print(resp.text)
            return False

        print("No issue detected on home page")
        return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    if not reproduce():
        sys.exit(1)
    else:
        sys.exit(0)
