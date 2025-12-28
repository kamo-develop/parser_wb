import asyncio
from typing import List, Dict
from urllib.parse import quote

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from config import conf
from context_manager import create_contexts_with_proxy, create_one_context
from utils import is_antibot_page, emulate_scroll_to_bottom_page


async def parse_catalog_page(page: Page, url: str) -> List[str]:
    """
    Парсинг страницы каталога товаров
    """
    await page.goto(url)

    card_wrapper = page.locator("div.product-card__wrapper").first
    await card_wrapper.wait_for(state="visible")
    await emulate_scroll_to_bottom_page(page)

    if await is_antibot_page(page):
        logger.error(f"Found antibot page {url}")

    cards_wrapper = page.locator("div.product-card-list div.product-card__wrapper")
    product_cards = await cards_wrapper.all()
    links = []
    for card in product_cards:
        card_link = card.locator("a.product-card__link").first
        links.append(await card_link.get_attribute("href"))

    logger.info(f"Found {len(links)} product cards")
    return links


async def catalog_page_parsing_task(context, queue: asyncio.Queue, product_links: List[str]):
    page: Page = await context.new_page()
    try:
        while True:
            try:
                url = await asyncio.wait_for(queue.get(), timeout=40)
            except asyncio.TimeoutError:
                # Задачи закончены
                break

            try:
                logger.debug(f"Parsing catalog page {url}")
                links = await parse_catalog_page(page, url)
                product_links.extend(links)
            except PlaywrightTimeoutError:
                # Будет попытка ещё раз обработать страницу
                logger.error(f"Parse catalog Timeout. Retry load page {url}")
                await queue.put(url)
                continue
            except Exception:
                logger.exception(f"Parse catalog Error. Skip page {url}")
            finally:
                queue.task_done()
    finally:
        await page.close()


async def run_catalog_parsing_tasks(browser) -> List[str]:
    base_search_url = "https://www.wildberries.ru/catalog/0/search.aspx"
    link_catalog_pages = [
        f"{base_search_url}?page={page}&search={quote(conf.query)}"
        for page in range(conf.page_num_start, conf.page_num_end + 1)
    ]
    logger.info(f"Start parsing catalog pages from {conf.page_num_start} to {conf.page_num_end}")

    queue: asyncio.Queue = asyncio.Queue()
    for link in link_catalog_pages:
        await queue.put(link)

    product_links: List[str] = []

    context = await create_one_context(browser)
    # Один контекст (один прокси), чтобы не ловить дубли
    tasks = []
    for i in range(conf.pages_per_context):
        # На один контекст несколько задач (страниц)
        tasks.append(asyncio.create_task(catalog_page_parsing_task(context, queue, product_links)))

    try:
        await asyncio.gather(*tasks)
        return product_links
    except Exception:
        logger.exception("Error parsing")
    finally:
        try:
            await context.close()
        except Exception:
            logger.exception("Context closing failed")
    return []