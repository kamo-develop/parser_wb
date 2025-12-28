import asyncio

from loguru import logger
from playwright.async_api import async_playwright

from catalog_tasks import run_catalog_parsing_tasks
from config import conf
from export_data import save_data
from product_tasks import run_product_parsing_tasks


#
# async def search_product_links(browser) -> List[str]:
#     context = await make_new_context(browser, proxy=conf.proxies[0], user_agent=USER_AGENT)
#     page: Page = await context.new_page()
#     search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote(conf.query)}"
#
#     try:
#         await page.goto(search_url)
#         card_wrapper = page.locator("div.product-card__wrapper").first
#         await card_wrapper.wait_for(state="visible")
#         logger.debug(f"Found first card__wrapper")
#         await emulate_scroll_to_bottom_page(page)
#         logger.debug(f"End page")
#
#         if await is_antibot_page(page):
#             logger.error(f"Found antibot page {search_url}")
#
#         cards_wrapper = page.locator("div.product-card-list div.product-card__wrapper")
#         product_cards = await cards_wrapper.all()
#         links = []
#         for card in product_cards:
#             card_link = card.locator("a.product-card__link").first
#             links.append(await card_link.get_attribute("href"))
#
#         await run_product_parsing_tasks(browser, links[:20])
#
#         logger.debug(f"Found {len(links)} links")
#         logger.debug(links)
#     except Exception:
#         logger.exception("Search failed")
#     finally:
#         await page.close()
#         await context.close()
#
#     return []


async def main():
    logger.debug(f"{conf}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        # Получить ссылки на товары со страниц каталога
        product_links = await run_catalog_parsing_tasks(browser)

        # Парсинг страниц товаров
        results = await run_product_parsing_tasks(browser, product_links)

        # Сохранение данных
        save_data(results)

        # await run_product_parsing_tasks(browser, [
        #                       'https://www.wildberries.ru/catalog/287755147/detail.aspx',
        #                       'https://www.wildberries.ru/catalog/39188958/detail.aspx',
        #                       'https://www.wildberries.ru/catalog/288989036/detail.aspx',
        #                       'https://www.wildberries.ru/catalog/452846226/detail.aspx',
        #                       'https://www.wildberries.ru/catalog/542553011/detail.aspx',
        #                       'https://www.wildberries.ru/catalog/250318267/detail.aspx',
        #                       'https://www.wildberries.ru/catalog/46824972/detail.aspx',
        #                       'https://www.wildberries.ru/catalog/306851990/detail.aspx',
        #                       'https://www.wildberries.ru/catalog/547852764/detail.aspx',
        #                       'https://www.wildberries.ru/catalog/614672895/detail.aspx',
        #
        #                   ])

if __name__ == '__main__':
    asyncio.run(main())

