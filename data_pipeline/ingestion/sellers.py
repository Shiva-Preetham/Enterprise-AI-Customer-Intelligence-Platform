"""Seller ingestion — olist_sellers_dataset.csv → raw.sellers."""

from __future__ import annotations

from backend.models.sellers import Seller
from data_pipeline.ingestion.base import BaseIngester


class SellerIngester(BaseIngester):
    entity_name = "sellers"
    csv_filename = "olist_sellers_dataset.csv"
    required_columns = [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ]
    model_class = Seller
