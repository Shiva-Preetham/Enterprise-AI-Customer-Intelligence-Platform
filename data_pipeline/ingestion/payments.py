"""Payment ingestion — olist_order_payments_dataset.csv → raw.payments."""

from __future__ import annotations

import pandas as pd

from backend.models.payments import Payment
from data_pipeline.ingestion.base import BaseIngester


class PaymentIngester(BaseIngester):
    entity_name = "payments"
    csv_filename = "olist_order_payments_dataset.csv"
    required_columns = [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ]
    model_class = Payment

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert numerics."""
        df = super()._clean_dataframe(df)

        df["payment_sequential"] = pd.to_numeric(df["payment_sequential"])
        df["payment_installments"] = pd.to_numeric(df["payment_installments"])
        df["payment_value"] = pd.to_numeric(df["payment_value"])

        return df
