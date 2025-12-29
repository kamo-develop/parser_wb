import asyncio
from typing import List, Dict, Any

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from playwright.async_api import Error as PlaywrightError

from config import conf
from context_manager import create_contexts_with_proxy
from export_data import save_data
from parse_product import parse_product_page
from utils import random_sleep


async def product_parsing_task(context, queue: asyncio.Queue, results: List[Dict[str, Any]]):
    page: Page = await context.new_page()
    try:
        while True:
            # Пока в очереди есть ссылки, задача работает
            try:
                url = await asyncio.wait_for(queue.get(), timeout=40)
            except asyncio.TimeoutError:
                # Задачи закончены
                break

            try:
                data = {}
                for i in range(3):
                    data, success = await parse_product_page(page, url)
                    if success:
                        break
                    else:
                        logger.debug(f"Attempt {i+1} not success {url}")
                results.append(data)
                logger.info(f"Success parsed product page {url}")
            except PlaywrightTimeoutError:
                # Будет попытка ещё раз обработать страницу
                logger.error(f"Parse product Timeout. Retry load page {url}")
                await random_sleep(1, 3)
                await queue.put(url)
                continue
            except PlaywrightError:
                logger.exception(f"Playwright network error. Retry load page {url}")
                await random_sleep(3, 5)
                # Перезапуск страницы
                await page.close()
                page: Page = await context.new_page()
                await queue.put(url)
                continue
            except Exception:
                logger.exception(f"Parse product Error. Skip page {url}")
            finally:
                queue.task_done()
    finally:
        await page.close()


async def run_product_parsing_tasks(browser, links: List[str]) -> List[Dict[str, Any]]:
    queue: asyncio.Queue = asyncio.Queue()
    for link in links:
        await queue.put(link)

    contexts = await create_contexts_with_proxy(browser)

    results: List[Dict[str, Any]] = []
    tasks = []
    for context in contexts:
        for i in range(conf.pages_per_context):
            # На один контекст несколько задач (страниц)
            tasks.append(asyncio.create_task(product_parsing_task(context, queue, results)))

    try:
        await asyncio.gather(*tasks)
        return results
    except Exception:
        logger.exception("Error parsing")
    finally:
        for context in contexts:
            try:
                await context.close()
            except Exception:
                logger.exception("Context closing failed")
    return []
