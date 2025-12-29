import os
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from config import conf


COLUMN_RENAME_MAP = {
    "url": "Ссылка на товар",
    "article": "Артикул",
    "title": "Название",
    "price": "Цена",
    "description": "Описание",
    "images": "Ссылки на изображения",
    "seller_name": "Название селлера",
    "seller_link": "Ссылка на селлера",
    "sizes": "Размеры",
    "remains": "Остатки по товару",
    "rating": "Рейтинг",
    "count_reviews": "Количество отзывов",
}



def save_data(results: List[Dict[str, Any]]):
    results = [r for r in results if r is not None]
    df_main = pd.DataFrame(results).drop(columns=["characteristics"])
    df_char = pd.json_normalize([item.get("characteristics", {}) for item in results])
    df = pd.concat([df_main, df_char], axis=1)

    # Фильтрация по критериям
    df_filtered = df[
        (df["rating"] >= conf.filtered_rating) &
        (df["price"] <= conf.filtered_price) &
        (df["Страна производства"] == conf.filtered_country)
        ].copy()

    df.rename(columns=COLUMN_RENAME_MAP, inplace=True)
    df_filtered.rename(columns=COLUMN_RENAME_MAP, inplace=True)

    root_dir = Path(__file__).resolve().parents[1]
    output_dir = root_dir / conf.output_path
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_dir / "full_catalog.xlsx", index=False)
    df_filtered.to_excel(output_dir / "filtered_catalog.xlsx", index=False)

