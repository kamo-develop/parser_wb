import os
from typing import List, Dict, Any
import pandas as pd
from config import conf


def save_data(results: List[Dict[str, Any]]):
    results = [r for r in results if r is not None]
    df_main = pd.DataFrame(results).drop(columns=["characteristics"])
    df_char = pd.json_normalize([item.get("characteristics", {}) for item in results])
    df = pd.concat([df_main, df_char], axis=1)
    full_path = os.path.join(conf.output_path, "full_catalog.xlsx")
    df.to_excel(full_path, index=False)

    # Фильтрация по критериям
    df_filtered = df[
        (df["rating"] >= conf.filtered_rating) &
        (df["price"] <= conf.filtered_price) &
        (df["Страна производства"] == conf.filtered_country)
        ].copy()
    full_path = os.path.join(conf.output_path, "filtered_catalog.xlsx")
    df_filtered.to_excel(full_path, index=False)

