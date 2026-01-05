
import asyncio
from playwright.async_api import async_playwright
import threading
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
from wsgiref.simple_server import make_server
from app import create_app, db
from app.models import User, UserRole
from werkzeug.security import generate_password_hash
from config import TestingConfig

# --- Test Setup ---
# It's recommended to use a separate test database
# For this script, we'll use an in-memory SQLite database for simplicity
app = create_app(TestingConfig)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['SERVER_NAME'] = 'localhost:5000'

def run_app():
    with app.app_context():
        db.create_all()
        # Create a test user if one doesn't exist
        if not User.query.filter_by(username='testuser').first():
            user = User(username='testuser', email='test@example.com', password_hash=generate_password_hash('password'), role=UserRole.USER)
            db.session.add(user)
        # Create an admin user if one doesn't exist
        if not User.query.filter_by(username='adminuser').first():
            admin = User(username='adminuser', email='admin@example.com', password_hash=generate_password_hash('password'), role=UserRole.ADMIN)
            db.session.add(admin)
        db.session.commit()

    # Use WSGI server instead of app.run for better control in a thread
    server = make_server('localhost', 5000, app)
    print("Starting server on http://localhost:5000")
    server.serve_forever()


async def main():
    server_thread = threading.Thread(target=run_app)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # Give the server a moment to start

    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # --- Test Case 1: Standard User ---
        page_user = await browser.new_page()
        await page_user.goto("http://localhost:5000/auth/login")
        await page_user.fill('input[name="username"]', "testuser")
        await page_user.fill('input[name="password"]', "password")
        await page_user.get_by_role("button", name="Sign In").click()
        await page_user.wait_for_url("http://localhost:5000/")
        await page_user.screenshot(path="/home/jules/verification/navigation_user.png")

        # Verification for standard user
        dashboards_visible_user = await page_user.is_visible('a:has-text("Dashboards")')
        if dashboards_visible_user:
            print("Verification failed for standard user: Dashboards link is visible.")
        else:
            print("Verification successful for standard user: Dashboards link is not visible.")

        # --- Test Case 2: Admin User ---
        page_admin = await browser.new_page()
        await page_admin.goto("http://localhost:5000/auth/login")
        await page_admin.fill('input[name="username"]', "adminuser")
        await page_admin.fill('input[name="password"]', "password")
        await page_admin.get_by_role("button", name="Sign In").click()
        await page_admin.wait_for_url("http://localhost:5000/")
        await page_admin.screenshot(path="/home/jules/verification/navigation_admin.png")

        # Verification for admin user
        dashboards_visible_admin = await page_admin.is_visible('a:has-text("Dashboards")')
        if dashboards_visible_admin:
            print("Verification successful for admin user: Dashboards link is visible.")
        else:
            print("Verification failed for admin user: Dashboards link is not visible.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
