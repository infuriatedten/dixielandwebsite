import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            # Login
            await page.goto("http://127.0.0.1:5000/auth/login")
            await page.fill('input[name="username"]', "new_admin")
            await page.fill('input[name="password"]', "password")
            await page.get_by_role("button", name="Sign In").click()
            await page.wait_for_url("http://127.0.0.1:5000/home")

            # Go to manage users page
            await page.goto("http://127.0.0.1:5000/admin/users")
            await page.screenshot(path="screenshots/user_list_before_edit_click.png")


            # Click the first edit button on the page
            await page.locator('a.btn-primary:has-text("Edit")').first.click()

            # Wait for the edit page to load
            await page.wait_for_url("http://127.0.0.1:5000/admin/user/1/edit")

            # Change pay rate
            await page.fill('input[name="pay_rate"]', "25.50")
            await page.get_by_role("button", name="Update User").click()

            # The user is redirected to the /admin/users page, wait for it
            await page.wait_for_url("http://127.0.0.1:5000/admin/users")

            # Take screenshot after changes
            await page.screenshot(path="screenshots/user_list_after_final.png")

        except Exception as e:
            print(f"An error occurred: {e}")
            await page.screenshot(path="screenshots/error.png")

        finally:
            await browser.close()

asyncio.run(main())
