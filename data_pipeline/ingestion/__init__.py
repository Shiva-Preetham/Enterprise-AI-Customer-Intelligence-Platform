"""Data Ingestion Package — Modular CSV-to-PostgreSQL loaders."""

from data_pipeline.ingestion.loader import run_ingestion

__all__ = ["run_ingestion"]
