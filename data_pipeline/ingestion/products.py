"""Product ingestion — olist_products_dataset.csv → raw.products."""

from __future__ import annotations

import pandas as pd

from backend.models.products import Product
from data_pipeline.ingestion.base import BaseIngester


class ProductIngester(BaseIngester):
    entity_name = "products"
    csv_filename = "olist_products_dataset.csv"
    required_columns = [
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]
    model_class = Product

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Custom cleaning for products: handle empty strings in numeric columns."""
        df = super()._clean_dataframe(df)

        # The dataset contains empty strings for missing dimensions/weights instead of nulls.
        numeric_cols = [
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # SQLAlchemy handles pandas NaNs well, but we can replace with None to be sure
            df[col] = df[col].replace({float('nan'): None})

        # Replace empty strings with None for category
        df["product_category_name"] = df["product_category_name"].replace({"": None})
        return df
