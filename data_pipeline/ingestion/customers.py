"""Customer ingestion — olist_customers_dataset.csv → raw.customers."""

from __future__ import annotations

from backend.models.customers import Customer
from data_pipeline.ingestion.base import BaseIngester


class CustomerIngester(BaseIngester):
    entity_name = "customers"
    csv_filename = "olist_customers_dataset.csv"
    required_columns = [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ]
    model_class = Customer
