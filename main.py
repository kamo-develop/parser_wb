import asyncio
from typing import List, Dict, Any
from urllib.parse import quote

from loguru import logger
from playwright.async_api import async_playwright, Page

from config import conf
from utils import random_sleep, is_antibot_page, emulate_user_actions, emulate_scroll_to_bottom_page

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0"

async def make_new_context(browser, proxy, user_agent):
    return await browser.new_context(
        proxy=proxy,
        user_agent=user_agent,
        viewport={"width": 1366, "height": 768},
        locale="ru-RU",
        timezone_id="Europe/Moscow",
    )


async def parse_product_page(page: Page, link: str):
    try:
        await page.goto(url=link)
        await page.wait_for_selector(
            "div.product-page > div:nth-of-type(3) > div:nth-of-type(3)",
            timeout=15000
        )
        await emulate_user_actions(page)
        logger.debug(await page.title())
    except Exception:
        logger.exception("Parse product page failed")


async def worker_task(context, queue: asyncio.Queue, results: List[Dict[str, Any]]):
    page: Page = await context.new_page()
    try:
        while True:
            try:
                url = await asyncio.wait_for(queue.get(), timeout=5)
                data = await parse_product_page(page, url)
            except asyncio.TimeoutError:
                break
    except Exception:
        logger.exception("Worker failed")
    finally:
        await page.close()


async def run_workers(browser, links: List[str]):
    queue: asyncio.Queue = asyncio.Queue()
    for link in links:
        await queue.put(link)

    contexts = []
    for i in range(conf.count_workers):
        proxy = conf.proxies[i % len(conf.proxies)]
        context = await make_new_context(browser, proxy, USER_AGENT)
        contexts.append(context)

    results: List[Dict[str, Any]] = []
    tasks = [asyncio.create_task(worker_task(context, queue, results)) for context in contexts]

    try:
        await asyncio.gather(*tasks)
    finally:
        for context in contexts:
            try:
                await context.close()
            except Exception:
                logger.exception("Context closing failed")


async def search_product_links(browser) -> List[str]:
    context = await make_new_context(browser, proxy=conf.proxies[0], user_agent=USER_AGENT)
    page: Page = await context.new_page()
    search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote(conf.query)}"

    try:
        await page.goto(search_url)
        await page.wait_for_selector(
            "div.product-card__wrapper",
            timeout=15000
        )
        logger.debug(f"Found first card__wrapper")
        await emulate_scroll_to_bottom_page(page)
        logger.debug(f"End page")

        if await is_antibot_page(page):
            logger.error(f"Found antibot page {search_url}")

        product_cards = await page.query_selector_all("div.product-card-list div.product-card__wrapper")
        links = []
        for card in product_cards:
            link = await card.query_selector("a.product-card__link")
            links.append(await link.get_attribute("href"))

        # await run_workers(browser, links)

        logger.debug(f"Found {len(links)} links")
        logger.debug(links)
    except Exception:
        logger.exception("Search failed")
    finally:
        await page.close()
        await context.close()

    return []


async def main():
    logger.debug(f"{conf}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        # await search_product_links(browser)
        await run_workers(browser,
                          [
                              'https://www.wildberries.ru/catalog/39188958/detail.aspx',
                              'https://www.wildberries.ru/catalog/452846226/detail.aspx',
                              'https://www.wildberries.ru/catalog/287755147/detail.aspx',
                              'https://www.wildberries.ru/catalog/542553011/detail.aspx',
                              'https://www.wildberries.ru/catalog/250318267/detail.aspx',
                              'https://www.wildberries.ru/catalog/46824972/detail.aspx',
                              'https://www.wildberries.ru/catalog/306851990/detail.aspx',
                              'https://www.wildberries.ru/catalog/547852764/detail.aspx',
                              'https://www.wildberries.ru/catalog/614672895/detail.aspx',
                              'https://www.wildberries.ru/catalog/288989036/detail.aspx'
                          ]
                          )

if __name__ == '__main__':
    asyncio.run(main())

