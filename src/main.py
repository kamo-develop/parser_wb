import asyncio
from pathlib import Path

from loguru import logger
from playwright.async_api import async_playwright

from catalog_tasks import run_catalog_parsing_tasks
from config import conf
from export_data import save_data
from product_tasks import run_product_parsing_tasks
from utils import count_unique_links, find_duplicate_links, remove_duplicate_links

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.add(
    LOG_DIR / "app.log",
    level="DEBUG",
    encoding="utf-8"
)


async def main():
    logger.info(f"Configuration:\n{conf}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        # Получить ссылки на товары со страниц каталога
        product_links = await run_catalog_parsing_tasks(browser)

        count_unique = count_unique_links(product_links)
        duplicate_links = find_duplicate_links(product_links)
        logger.debug(f"Duplicate links: {duplicate_links}")
        logger.info(f"Found {len(product_links)} products ({count_unique} unique)")
        product_unique_links = remove_duplicate_links(product_links)
        logger.info(f"Total count unique products: {len(product_unique_links)}")


        # Парсинг страниц товаров
        results = await run_product_parsing_tasks(browser, product_unique_links)
        logger.info(f"Parsed {len(results)} products")

        # Сохранение данных
        save_data(results)
        logger.info(f"Saved {len(results)} products")

if __name__ == '__main__':
    asyncio.run(main())

