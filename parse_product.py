import re
from typing import Dict, Tuple

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from utils import emulate_user_actions


def get_article_from_url(url: str) -> str:
    """
    Получить артикул из ссылки на товар
    """
    try:
        return url.split("/catalog/")[1].split("/")[0]
    except Exception:
        logger.exception(f"get_article_from_url failed {url}")
    return ""


async def get_product_title(page: Page, url: str) -> str:
    """
    Получить название товара
    """
    try:
        block = page.locator("div[class^=mainWrap-] h3").first
        await block.wait_for(state="visible")
        return await block.inner_text()
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading title {url}")
    except Exception:
        logger.exception(f"get_product_title failed {url}")
    return ""


async def get_product_price(page: Page, url: str) -> float:
    """
    Получить цену товара
    """
    try:
        block = page.locator("div[class^=productPageAside-] h2").first
        if await block.count() == 0:
            block = page.locator('span[class^=priceBlockPrice-]').first
        await block.wait_for(state="visible")
        price_text = await block.inner_text()
        return float(re.sub(r"[^\d.,]", "", price_text).replace(",", "."))
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading price {url}")
    except Exception:
        logger.exception(f"get_product_price failed {url}")
    return 0.0


async def click_characteristic_button(page: Page, url: str):
    try:
        # Получить кнопку
        desc_button = page.locator('div[class^="mainWrap-"] div[class^="options-"] div.mo-button__text-content').first
        await desc_button.wait_for(state="visible")
        await desc_button.click()
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while click characteristic button {url}")
    except Exception:
        logger.exception(f"click_characteristic_button failed {url}")

async def get_product_description(page: Page, url: str) -> str:
    """
    Получить описание товара
    """
    try:
        await click_characteristic_button(page, url)
        # Дождаться прогрузки окна
        modal = page.locator('div.mo-modal__wrapper div[class^="content-"]').first
        await modal.wait_for(state="visible")
        return await modal.locator("section#section-description").first.inner_text()
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading description {url}")
    except Exception:
        logger.exception(f"get_product_description failed {url}")
    return ""


async def get_product_images(page: Page, url: str) -> str:
    """
    Получить изображения товара
    """
    try:
        # Получить кнопку
        image_blocks = page.locator("div[class^=mediaSlider-] div.swiper-slide img")
        images = await image_blocks.all()
        img_links = []
        for image in images:
            try:
                img_links.append(await image.get_attribute("src"))
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout while loading one image {url}")
            except Exception:
                logger.exception(f"product_image failed {url}")

        return ", ".join(img_links)
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading imagees {url}")
    except Exception:
        logger.exception(f"get_product_images failed {url}")
    return ""



async def get_product_characteristic(page: Page, url: str) -> Dict[str, str]:
    """
    Получить описание товара
    """
    try:
        modal = page.locator('div.mo-modal__wrapper div[class^="content-"]')
        if await modal.count() == 0:
            await click_characteristic_button(page, url)
        await modal.first.wait_for(state="visible")
        rows = await modal.first.locator("table tr").all()
        characteristics = {}
        for row in rows:
            try:
                key = await row.locator("th").first.inner_text()
                value = await row.locator("td").first.inner_text()
                characteristics[key] = value
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout while loading one row characteristic {url}")
            except Exception:
                logger.exception("characteristic failed {url}")
        return characteristics
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading characteristic {url}")
    except Exception:
        logger.exception(f"get_product_characteristic failed {url}")
    return {}


async def get_product_seller(page: Page, url: str) -> Tuple[str, str]:
    """
    Получить название и ссылку на селлера
    """
    try:
        block = page.locator("div[class^=sellerInfoWrap-] a").first
        await block.wait_for(state="visible")
        link = await block.get_attribute("href")
        block_name = block.locator("div[class^=sellerInfoNameDefault-] span:nth-of-type(1)")
        await block_name.wait_for(state="visible")
        seller_name = await block_name.inner_text()
        return seller_name, link
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading seller {url}")
    except Exception:
        logger.exception(f"get_product_seller failed {url}")
    return ("", "")



async def get_product_sizes(page: Page, url: str) -> str:
    """
    Получить размеры товара
    """
    try:
        sizes_block = await page.locator("div[class^=mainWrap-] li[class^=sizesListItem-]").all()
        sizes = []
        for size in sizes_block:
            try:
                size1 = size.locator("span:nth-of-type(1)")
                await size1.wait_for(state="visible")
                size2 = size.locator("span:nth-of-type(2)")
                await size2.wait_for(state="visible")
                sizes.append((await size1.inner_text(), await size2.inner_text()))
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout while loading one size {url}")
            except Exception:
                logger.exception(f"product_size failed {url}")

        return ", ".join(f"{size1} ({size2})" for size1, size2 in sizes)
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading sizes {url}")
    except Exception:
        logger.exception(f"get_product_sizes failed {url}")
    return ""


async def get_product_remains(page: Page, url: str):
    """
    Получить остатки товара
    """
    try:
        block = page.locator("div[class^=qtyThermometer-] span")
        if await block.count() == 0:
            block = page.locator("div[class^=productSummary-] div.mo-badge__content span")
            if await block.count() == 0:
                return "-"
        await block.first.wait_for(state="visible")
        remains = await block.first.inner_text()
        if (remains.startswith("Осталось")
                or remains.startswith("осталось")
                or remains.startswith("Осталась")
                or remains.startswith("осталась")
                or remains.startswith("Остались")
                or remains.startswith("остались")
        ):
            remains_count = int(re.findall(r'\d+', remains)[0])
            return remains_count
        else:
            return "-"
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading remains {url}")
    except Exception:
        logger.exception(f"get_product_remains failed {url}")
    return "-"



async def get_product_rating(page: Page, url: str) -> Tuple[float, int]:
    """
    Получить рейтинг и кол-во отзывов
    """
    try:
        block = page.locator("div[class^=productCommonInfo-] a:nth-of-type(1) span").first
        await block.wait_for(state="visible")
        rating_str = await block.inner_text()

        match = re.search(r'(\d+[\.,]?\d*)\s*[·•\-]\s*([\d\s]+)', rating_str)
        if not match:
            return 0.0, 0
        rating_str_clean = match.group(1).replace(',', '.')
        rating = float(rating_str_clean)

        count_str = match.group(2)
        count_str_clean = re.sub(r'\s', '', count_str)
        count = int(count_str_clean)

        return rating, count
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading rating {url}")
    except Exception:
        logger.exception(f"get_product_rating failed {url}")
    return 0.0, 0


async def parse_product_page(page: Page, url: str):
    """
    Парсинг страницы товара
    """
    data = {}
    await page.goto(url=url)
    block = page.locator("div[class^=productPageAside-]").first
    await block.wait_for(state="visible")
    await emulate_user_actions(page)

    data["url"] = url
    data["article"] = get_article_from_url(url)
    data["title"] = await get_product_title(page, url)
    data["price"] = await get_product_price(page, url)
    data["description"] = await get_product_description(page, url)
    data["images"] = await get_product_images(page, url)
    data["characteristics"] = await get_product_characteristic(page, url)
    seller_name, seller_link = await get_product_seller(page, url)
    data["seller_name"] = seller_name
    data["seller_link"] = "https://www.wildberries.ru" + seller_link
    data["sizes"] = await get_product_sizes(page, url)
    data["remains"] = await get_product_remains(page, url)
    rating, count_reviews = await get_product_rating(page, url)
    data["rating"] = rating
    data["count_reviews"] = count_reviews

    return data