import re
from typing import Dict, Tuple, Any

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


async def get_product_title(page: Page, url: str) -> tuple[str, bool]:
    """
    Получить название товара
    """
    try:
        block = page.locator("div[class^=mainWrap-] h3").first
        await block.wait_for(state="visible")
        return await block.inner_text(), True
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading title {url}")
        return "", False
    except Exception:
        logger.exception(f"get_product_title failed {url}")
    return "", True


async def get_product_price(page: Page, url: str) -> tuple[float, bool]:
    """
    Получить цену товара
    """
    try:
        block = page.locator("div[class^=productPageAside-] h2").first
        if await block.count() == 0:
            block = page.locator('span[class^=priceBlockPrice-]').first
        await block.wait_for(state="visible")
        price_text = await block.inner_text()
        return float(re.sub(r"[^\d.,]", "", price_text).replace(",", ".")), True
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading price {url}")
        return 0.0, False
    except Exception:
        logger.exception(f"get_product_price failed {url}")
    return 0.0, True


async def click_characteristic_button(page: Page, url: str):
    try:
        # Получить кнопку
        desc_button = page.locator('div[class^="mainWrap-"] div[class^="options-"] div.mo-button__text-content').first
        await desc_button.wait_for(state="visible")
        await desc_button.click()
    except PlaywrightTimeoutError as e:
        logger.warning(f"Timeout while click characteristic button {url}")
        raise e
    except Exception:
        logger.exception(f"click_characteristic_button failed {url}")

async def get_product_description(page: Page, url: str) -> tuple[str, bool]:
    """
    Получить описание товара
    """
    try:
        await click_characteristic_button(page, url)
        # Дождаться прогрузки окна
        modal = page.locator('div.mo-modal__wrapper div[class^="content-"]').first
        await modal.wait_for(state="visible")
        desc_text = await modal.locator("section#section-description").first.inner_text()

        if desc_text.startswith("Описание"):
            desc_clean = desc_text[len("Описание"):].strip()
        else:
            desc_clean = desc_text.strip()
        return desc_clean, True
    except PlaywrightTimeoutError as e:
        logger.warning(f"Timeout while loading description {url}")
        return "", False
    except Exception:
        logger.exception(f"get_product_description failed {url}")
    return "", True


async def get_product_images(page: Page, url: str) -> tuple[str, bool]:
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

        return ", ".join(img_links), True
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading imagees {url}")
        return "", False
    except Exception:
        logger.exception(f"get_product_images failed {url}")
    return "", True



async def get_product_characteristic(page: Page, url: str) -> tuple[dict[Any, Any], bool]:
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
        return characteristics, True
    except PlaywrightTimeoutError as e:
        logger.warning(f"Timeout while loading characteristic {url}")
        return {}, False
    except Exception:
        logger.exception(f"get_product_characteristic failed {url}")
    return {}, True


async def get_product_seller(page: Page, url: str) -> tuple[str, str, bool]:
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
        return seller_name, link, True
    except PlaywrightTimeoutError as e:
        logger.warning(f"Timeout while loading seller {url}")
        return "", "", False
    except Exception:
        logger.exception(f"get_product_seller failed {url}")
    return "", "", True



async def get_product_sizes(page: Page, url: str) -> tuple[str, bool]:
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

        return ", ".join(f"{size1} ({size2})" for size1, size2 in sizes), True
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading sizes {url}")
        return "", False
    except Exception:
        logger.exception(f"get_product_sizes failed {url}")
    return "", True


async def get_product_remains(page: Page, url: str) -> tuple[Any, bool]:
    """
    Получить остатки товара
    """
    try:
        block = page.locator("div[class^=qtyThermometer-] span")
        if await block.count() == 0:
            block = page.locator("div[class^=productSummary-] div.mo-badge__content span")
            if await block.count() == 0:
                return "-", True
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
            return remains_count, True
        else:
            return "-", True
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading remains {url}")
        return "", False
    except Exception:
        logger.exception(f"get_product_remains failed {url}")
    return "-", True



async def get_product_rating(page: Page, url: str) -> tuple[float, int, bool]:
    """
    Получить рейтинг и кол-во отзывов
    """
    try:
        block = page.locator("div[class^=productCommonInfo-] a:nth-of-type(1) span").first
        await block.wait_for(state="visible")
        rating_str = await block.inner_text()

        match = re.search(r'(\d+[\.,]?\d*)\s*[·•\-]\s*([\d\s]+)', rating_str)
        if not match:
            return 0.0, 0, True
        rating_str_clean = match.group(1).replace(',', '.')
        rating = float(rating_str_clean)

        count_str = match.group(2)
        count_str_clean = re.sub(r'\s', '', count_str)
        count = int(count_str_clean)

        return rating, count, True
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout while loading rating {url}")
        return 0.0, 0, False
    except Exception:
        logger.exception(f"get_product_rating failed {url}")
    return 0.0, 0, True


async def parse_product_page(page: Page, url: str) -> tuple[dict[Any, Any], bool]:
    """
    Парсинг страницы товара
    """
    data = {}
    success = {}
    await page.goto(url=url)
    block = page.locator("div[class^=productPageAside-]").first
    await block.wait_for(state="visible")
    await emulate_user_actions(page)

    data["url"] = url
    data["article"] = get_article_from_url(url)
    data["title"], success["title"] = await get_product_title(page, url)
    data["price"], success["price"] = await get_product_price(page, url)
    data["description"], success["description"] = await get_product_description(page, url)
    data["images"], success["images"] = await get_product_images(page, url)
    data["characteristics"], success["characteristics"] = await get_product_characteristic(page, url)
    seller_name, seller_link, success["seller"] = await get_product_seller(page, url)
    data["seller_name"] = seller_name
    data["seller_link"] = "https://www.wildberries.ru" + seller_link
    data["sizes"], success["sizes"] = await get_product_sizes(page, url)
    data["remains"], success["remains"] = await get_product_remains(page, url)
    rating, count_reviews, success["rating"] = await get_product_rating(page, url)
    data["rating"] = rating
    data["count_reviews"] = count_reviews

    all_success = all(success.values())
    return data, all_success