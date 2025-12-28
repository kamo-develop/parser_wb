import asyncio
from playwright.async_api import async_playwright
from config import conf


async def parse_with_proxy(browser, proxy):
    context = await browser.new_context(
        proxy=proxy
    )
    page = await context.new_page()

    try:
        await page.goto("https://api.ipify.org?format=json",)
        ip = await page.text_content("body")
        print(proxy, "->", ip)
    finally:
        await context.close()  # ВАЖНО

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        tasks = [
            parse_with_proxy(browser, proxy)
            for proxy in conf.proxies
        ]

        await asyncio.gather(*tasks)
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())