"""
Master Data Loader for Olist dataset.

Executes ingestion modules in topological order to satisfy Foreign Key constraints.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.engine import sync_engine
from backend.logging import get_logger, log_execution_time
from data_pipeline.ingestion.customers import CustomerIngester
from data_pipeline.ingestion.order_items import OrderItemIngester
from data_pipeline.ingestion.orders import OrderIngester
from data_pipeline.ingestion.payments import PaymentIngester
from data_pipeline.ingestion.products import ProductIngester
from data_pipeline.ingestion.reviews import ReviewIngester
from data_pipeline.ingestion.sellers import SellerIngester

logger = get_logger(__name__)

# Topological sort based on Foreign Key dependencies:
# 1. Customers, Sellers, Products have no FKs.
# 2. Orders depends on Customers.
# 3. OrderItems depends on Orders, Sellers, Products.
# 4. Payments depends on Orders.
# 5. Reviews depends on Orders.
INGESTION_ORDER = [
    CustomerIngester,
    SellerIngester,
    ProductIngester,
    OrderIngester,
    OrderItemIngester,
    PaymentIngester,
    ReviewIngester,
]


def run_ingestion() -> dict[str, dict[str, int | list[str]]]:
    """Execute the full dataset ingestion pipeline.

    Returns:
        A summary dictionary of the ingestion results for all entities.
    """
    logger.info("pipeline_started", mode="full_ingestion")
    
    results = {}
    
    with Session(sync_engine) as session:
        for ingester_cls in INGESTION_ORDER:
            ingester = ingester_cls(data_dir=settings.DATA_RAW_PATH)
            
            with log_execution_time(logger, f"ingest_{ingester.entity_name}"):
                result = ingester.ingest(session)
            
            if result.success:
                session.commit()
            else:
                session.rollback()
                logger.error("ingestion_aborted", entity=ingester.entity_name)
                # Fail fast on first error to prevent cascading FK errors
                break
                
            results[ingester.entity_name] = {
                "csv_rows": result.rows_in_csv,
                "inserted": result.rows_inserted,
                "skipped": result.rows_skipped_duplicate,
                "errors": result.errors,
            }

    logger.info("pipeline_finished", results=results)
    return results

if __name__ == "__main__":
    run_ingestion()
