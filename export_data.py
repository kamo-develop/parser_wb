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

    df_filtered = df[
        (df["rating"] >= 4.5) &
        (df["price"] <= 10000) &
        (df["Страна производства"] == "Россия")
        ].copy()
    full_path = os.path.join(conf.output_path, "filtered_catalog.xlsx")
    df_filtered.to_excel(full_path, index=False)

