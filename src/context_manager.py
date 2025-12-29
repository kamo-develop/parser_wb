from config import conf
from loguru import logger
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0"

async def make_new_context(browser, proxy, user_agent):
    context = await browser.new_context(
        proxy=proxy,
        user_agent=user_agent,
        viewport={"width": 1366, "height": 768},
        locale="ru-RU",
        timezone_id="Europe/Moscow",
    )
    context.set_default_timeout(timeout=60000)
    context.set_default_navigation_timeout(90000)
    logger.info(f"Made new context for proxy {proxy.get("server", "")}")
    return context

async def create_contexts_with_proxy(browser):
    contexts = []
    for i in range(conf.count_contexts):
        proxy = conf.proxies[i % len(conf.proxies)]
        context = await make_new_context(browser, proxy, USER_AGENT)
        contexts.append(context)
    return contexts

async def create_one_context(browser):
    proxy = conf.proxies[0]
    return await make_new_context(browser, proxy, USER_AGENT)