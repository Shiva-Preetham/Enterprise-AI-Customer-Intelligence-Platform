"""
Base ingestion module — shared logic for all entity loaders.

Every entity loader (customers.py, orders.py, etc.) inherits from
BaseIngester to avoid duplicating CSV reading, validation, and
insert logic. Each subclass only defines its entity-specific config:
table name, CSV filename, required columns, and the ORM model.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.db.base import SCHEMA_RAW, Base
from backend.logging import get_logger

logger = get_logger(__name__)


@dataclass
class IngestionResult:
    """Statistics returned by each ingestion module."""

    entity: str = ""
    rows_in_csv: int = 0
    rows_inserted: int = 0
    rows_skipped_duplicate: int = 0
    rows_skipped_error: int = 0
    errors: list[str] = field(default_factory=list)
    success: bool = True


class BaseIngester:
    """Base class for CSV-to-PostgreSQL ingestion.

    Subclasses must set:
        entity_name:      Human-readable name (e.g. "customers")
        csv_filename:      CSV file name in data/raw/
        required_columns:  List of columns that must exist in the CSV
        model_class:       SQLAlchemy ORM model
    """

    entity_name: str = ""
    csv_filename: str = ""
    required_columns: list[str] = []
    model_class: type[Base] | None = None

    def __init__(self, data_dir: str = "data/raw") -> None:
        self.data_dir = Path(data_dir)

    def _get_csv_path(self) -> Path:
        return self.data_dir / self.csv_filename

    def _validate_file(self, path: Path) -> list[str]:
        """Check file exists and is not empty."""
        errors: list[str] = []
        if not path.exists():
            errors.append(f"File not found: {path}")
        elif path.stat().st_size == 0:
            errors.append(f"File is empty: {path}")
        return errors

    def _validate_columns(self, df: pd.DataFrame) -> list[str]:
        """Check required columns are present."""
        missing = set(self.required_columns) - set(df.columns)
        if missing:
            return [f"Missing columns: {sorted(missing)}"]
        return []

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean data before insertion. Override in subclasses for custom logic."""
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].str.strip()
        return df

    def _get_primary_key_columns(self) -> list[str]:
        """Extract PK column names from the ORM model."""
        if self.model_class is None:
            return []
        mapper = self.model_class.__mapper__  # type: ignore[attr-defined]
        return [col.name for col in mapper.primary_key]

    def ingest(self, session: Session) -> IngestionResult:
        """Run the full ingestion pipeline for this entity.

        Steps:
            1. Validate CSV file exists and is non-empty
            2. Read CSV into DataFrame
            3. Validate required columns
            4. Clean data
            5. Deduplicate against existing DB records
            6. Bulk insert new records

        Args:
            session: A synchronous SQLAlchemy session.

        Returns:
            IngestionResult with statistics.
        """
        result = IngestionResult(entity=self.entity_name)
        csv_path = self._get_csv_path()

        # Step 1: Validate file
        file_errors = self._validate_file(csv_path)
        if file_errors:
            result.errors = file_errors
            result.success = False
            logger.error("file_validation_failed", entity=self.entity_name, errors=file_errors)
            return result

        # Step 2: Read CSV
        try:
            df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
        except Exception as e:
            result.errors.append(f"Failed to read CSV: {e}")
            result.success = False
            logger.error("csv_read_failed", entity=self.entity_name, error=str(e))
            return result

        result.rows_in_csv = len(df)
        logger.info("csv_loaded", entity=self.entity_name, rows=len(df))

        # Step 3: Validate columns
        col_errors = self._validate_columns(df)
        if col_errors:
            result.errors = col_errors
            result.success = False
            logger.error("column_validation_failed", entity=self.entity_name, errors=col_errors)
            return result

        # Step 4: Clean data
        df = self._clean_dataframe(df)

        # Step 5: Drop CSV-level duplicates (keep first)
        pk_cols = self._get_primary_key_columns()
        dupes_before = len(df)
        if pk_cols:
            df = df.drop_duplicates(subset=pk_cols, keep="first")
        csv_dupes = dupes_before - len(df)

        # Step 6: Check for existing records in DB
        if pk_cols and len(pk_cols) == 1:
            pk_col = pk_cols[0]
            table = f"{SCHEMA_RAW}.{self.model_class.__tablename__}"  # type: ignore[union-attr]
            existing = session.execute(
                text(f"SELECT {pk_col} FROM {table}")
            ).scalars().all()
            existing_set = set(existing)
            before_db_dedup = len(df)
            df = df[~df[pk_col].isin(existing_set)]
            result.rows_skipped_duplicate = csv_dupes + (before_db_dedup - len(df))
        else:
            result.rows_skipped_duplicate = csv_dupes

        # Step 7: Bulk insert
        if df.empty:
            logger.info("no_new_rows", entity=self.entity_name)
            result.rows_inserted = 0
            return result

        try:
            records = df.to_dict(orient="records")
            session.execute(
                self.model_class.__table__.insert(),  # type: ignore[union-attr]
                records,
            )
            session.flush()
            result.rows_inserted = len(records)
            logger.info(
                "rows_inserted",
                entity=self.entity_name,
                inserted=result.rows_inserted,
                skipped=result.rows_skipped_duplicate,
            )
        except Exception as e:
            result.errors.append(f"Insert failed: {e}")
            result.success = False
            logger.error("insert_failed", entity=self.entity_name, error=str(e))

        return result
