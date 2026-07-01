"""Review ingestion — olist_order_reviews_dataset.csv → raw.reviews."""

from __future__ import annotations

import pandas as pd

from backend.models.reviews import Review
from data_pipeline.ingestion.base import BaseIngester


class ReviewIngester(BaseIngester):
    entity_name = "reviews"
    csv_filename = "olist_order_reviews_dataset.csv"
    required_columns = [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ]
    model_class = Review

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert timestamps and numerics, handle empty texts."""
        df = super()._clean_dataframe(df)

        date_cols = ["review_creation_date", "review_answer_timestamp"]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce").replace({pd.NaT: None})

        df["review_score"] = pd.to_numeric(df["review_score"])

        # Replace empty strings with None
        text_cols = ["review_comment_title", "review_comment_message"]
        for col in text_cols:
            df[col] = df[col].replace({"": None})

        return df
