import asyncio
import random

from loguru import logger
from playwright.async_api import Page

from config import conf


async def random_sleep(a: float, b: float):
    await asyncio.sleep(random.uniform(a, b))



async def is_page_bottom(page: Page):
    scroll_y = await page.evaluate("window.scrollY")
    viewport_height = await page.evaluate("window.innerHeight")
    scroll_height = await page.evaluate("Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
    # logger.debug(f"scroll_y = {scroll_y} viewport_height = {viewport_height} Scroll height = {scroll_height}")
    return scroll_y + viewport_height >= scroll_height


async def emulate_scroll_to_bottom_page(page: Page):
    for i in range(conf.count_max_scroll):
        try:
            # Прокрутка
            await page.mouse.wheel(0, random.randint(300, 600))
            await page.mouse.move(
                random.randint(100, 600),
                random.randint(200, 600),
                steps=random.randint(5, 15)
            )
            # Задержка
            await random_sleep(*conf.random_pause_range)

            # Достигли конца страницы?
            if await is_page_bottom(page):
                break
        except Exception:
            logger.exception("Scroll exception")


async def emulate_user_actions(page: Page):
    await page.mouse.move(
        random.randint(100, 600),
        random.randint(200, 600)
    )
    await random_sleep(*conf.random_pause_range)


async def is_antibot_page(page: Page) -> bool:
    title = await page.title()
    if "Почти готово" in title:
        logger.debug("Почти готово")
        return True

    if await page.locator('script[src*="antibot"]').count() > 0:
        logger.debug('script[src*="antibot"]')
        return True

    if await page.locator("#wait_msg").count() > 0:
        logger.debug("wait_msg")
        return True

    return False