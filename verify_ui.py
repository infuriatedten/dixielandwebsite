import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://127.0.0.1:8000/auth/login")
        await page.wait_for_selector('input[name="username"]')
        await page.fill('input[name="username"]', "admin")
        await page.wait_for_selector('input[name="password"]')
        await page.fill('input[name="password"]', "adminpassword")
        await page.wait_for_selector('button[type="submit"]')
        await page.get_by_role("button", name="Sign In").click()
        await page.wait_for_url("http://127.0.0.1:8000/dashboard")
        await page.screenshot(path="dashboard_screenshot.png")
        await browser.close()

asyncio.run(main())
