"""Order ingestion — olist_orders_dataset.csv → raw.orders."""

from __future__ import annotations

import pandas as pd

from backend.models.orders import Order
from data_pipeline.ingestion.base import BaseIngester


class OrderIngester(BaseIngester):
    entity_name = "orders"
    csv_filename = "olist_orders_dataset.csv"
    required_columns = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    model_class = Order

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert timestamp strings to datetime objects."""
        df = super()._clean_dataframe(df)

        date_cols = [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df[col] = df[col].replace({pd.NaT: None})

        return df
