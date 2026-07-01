"""Order item ingestion — olist_order_items_dataset.csv → raw.order_items."""

from __future__ import annotations

import pandas as pd

from backend.models.order_items import OrderItem
from data_pipeline.ingestion.base import BaseIngester


class OrderItemIngester(BaseIngester):
    entity_name = "order_items"
    csv_filename = "olist_order_items_dataset.csv"
    required_columns = [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ]
    model_class = OrderItem

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert timestamps and numerics."""
        df = super()._clean_dataframe(df)

        df["shipping_limit_date"] = pd.to_datetime(
            df["shipping_limit_date"], errors="coerce"
        ).replace({pd.NaT: None})
        
        df["order_item_id"] = pd.to_numeric(df["order_item_id"])
        df["price"] = pd.to_numeric(df["price"])
        df["freight_value"] = pd.to_numeric(df["freight_value"])

        return df
