import asyncio
from typing import List, Dict, Any

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from context_manager import create_contexts_with_proxy
from export_data import save_data
from parse_product import parse_product_page


async def product_parsing_task(context, queue: asyncio.Queue, results: List[Dict[str, Any]]):
    page: Page = await context.new_page()
    try:
        while True:
            # Пока в очереди есть ссылки, задача работает
            try:
                url = await asyncio.wait_for(queue.get(), timeout=30)
            except asyncio.TimeoutError:
                # Задачи закончены
                break

            try:
                data = await parse_product_page(page, url)
                results.append(data)
                logger.info(f"Success parsed product page {url}")
            except PlaywrightTimeoutError:
                # Будет попытка ещё раз обработать страницу
                logger.exception(f"Parse product Timeout. Retry load page {url}")
                await queue.put(url)
                continue
            except Exception:
                logger.exception(f"Parse product Error. Skip page {url}")
                continue
            finally:
                try:
                    queue.task_done()
                except Exception:
                    pass
    except Exception:
        logger.exception("Task for product parsing failed")
    finally:
        await page.close()


async def run_product_parsing_tasks(browser, links: List[str]) -> List[Dict[str, Any]]:
    queue: asyncio.Queue = asyncio.Queue()
    for link in links:
        await queue.put(link)

    contexts = await create_contexts_with_proxy(browser)

    results: List[Dict[str, Any]] = []
    tasks = [asyncio.create_task(product_parsing_task(context, queue, results)) for context in contexts]

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
