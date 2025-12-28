import asyncio
from loguru import logger
from playwright.async_api import async_playwright

from catalog_tasks import run_catalog_parsing_tasks
from config import conf
from export_data import save_data
from product_tasks import run_product_parsing_tasks


async def main():
    logger.info(f"Configuration:\n{conf}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        # Получить ссылки на товары со страниц каталога
        product_links = await run_catalog_parsing_tasks(browser)
        logger.info(f"Found {len(product_links)} products")

        # Парсинг страниц товаров
        results = await run_product_parsing_tasks(browser, product_links)
        logger.info(f"Parsed {len(results)} products")

        # Сохранение данных
        save_data(results)
        logger.info(f"Saved {len(results)} products")

if __name__ == '__main__':
    asyncio.run(main())

