import asyncio
from typing import List
from urllib.parse import quote

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from config import conf
from context_manager import create_contexts_with_proxy
from utils import is_antibot_page, emulate_scroll_to_bottom_page


async def parse_catalog_page(page: Page, url: str) -> List[str]:
    """
    Парсинг страницы каталога товаров
    """
    await page.goto(url)

    card_wrapper = page.locator("div.product-card__wrapper").first
    await card_wrapper.wait_for(state="visible")
    logger.debug(f"Found first card__wrapper")
    await emulate_scroll_to_bottom_page(page)
    logger.debug(f"End page")

    if await is_antibot_page(page):
        logger.error(f"Found antibot page {url}")

    cards_wrapper = page.locator("div.product-card-list div.product-card__wrapper")
    product_cards = await cards_wrapper.all()
    links = []
    for card in product_cards:
        card_link = card.locator("a.product-card__link").first
        links.append(await card_link.get_attribute("href"))

    logger.debug(f"Found {len(links)} links")
    return links


async def catalog_page_parsing_task(context, queue: asyncio.Queue, product_links: List[str]):
    page: Page = await context.new_page()
    try:
        while True:
            try:
                url = await asyncio.wait_for(queue.get(), timeout=10)
            except asyncio.TimeoutError:
                # Задачи закончены
                break

            try:
                links = await parse_catalog_page(page, url)
                product_links.extend(links)
            except PlaywrightTimeoutError:
                # Будет попытка ещё раз обработать страницу
                logger.exception(f"Parse catalog Timeout. Retry load page {url}")
                await queue.put(url)
                continue
            except Exception:
                logger.exception(f"Parse catalog Error. Skip page {url}")
                continue
            finally:
                try:
                    queue.task_done()
                except Exception:
                    pass
    except Exception:
        logger.exception("Task for catalog page parsing failed")
    finally:
        await page.close()


async def run_catalog_parsing_tasks(browser) -> List[str]:
    base_search_url = "https://www.wildberries.ru/catalog/0/search.aspx"
    link_catalog_pages = [
        f"{base_search_url}?search={quote(conf.query)}?page={page}"
        for page in range(1, conf.count_pages + 1)
    ]

    queue: asyncio.Queue = asyncio.Queue()
    for link in link_catalog_pages:
        await queue.put(link)

    contexts = await create_contexts_with_proxy(browser)

    product_links: List[str] = []
    tasks = [asyncio.create_task(catalog_page_parsing_task(context, queue, product_links)) for context in contexts]

    try:
        await asyncio.gather(*tasks)
        return product_links
    except Exception:
        logger.exception("Error parsing")
    finally:
        for context in contexts:
            try:
                await context.close()
            except Exception:
                logger.exception("Context closing failed")
    return []
