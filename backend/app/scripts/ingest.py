#!/usr/bin/env python3
"""
CLI script for running real data ingestion from job APIs.

This script uses the existing IngestionService to fetch data from
The Muse and Remotive job APIs and persist it to the database.
"""

import asyncio
from datetime import datetime

from sqlalchemy import select

from app.clients.muse_client import MuseClient
from app.clients.remotive import RemotiveClient
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.data_source import DataSource
from app.services.ingestion_service import IngestionService


def get_or_create_source(session, code: str, name: str, base_url: str) -> DataSource:
    """Get existing data source or create a new one."""
    source = session.scalar(select(DataSource).where(DataSource.code == code))
    if source is None:
        source = DataSource(code=code, name=name, base_url=base_url)
        session.add(source)
        session.commit()
        session.refresh(source)
    return source


async def run_ingestion():
    """Run ingestion for all configured data sources."""
    print("Starting data ingestion...")

    # Load configuration
    settings = get_settings()

    # Create database session
    session = SessionLocal()

    try:
        # Get or create data sources
        muse_source = get_or_create_source(
            session, "muse", "The Muse", settings.muse_base_url
        )
        remotive_source = get_or_create_source(
            session, "remotive", "Remotive", settings.remotive_base_url
        )

        # Create API clients
        muse_client = MuseClient(settings)
        # Using default async client for Remotive
        remotive_client = RemotiveClient(settings)

        # Create ingestion service
        service = IngestionService(session, muse_client, remotive_client)

        # Run ingestion for both sources
        results = []

        # Muse ingestion (synchronous client in async context)
        print("Ingesting from The Muse...")
        try:
            muse_run = await service.ingest(muse_source)
            results.append(
                {
                    "source": "muse",
                    "name": "The Muse",
                    "status": muse_run.status,
                    "records": muse_run.records_received or 0,
                    "finished_at": muse_run.finished_at or datetime.now(),
                }
            )
        except Exception as e:
            results.append(
                {
                    "source": "muse",
                    "name": "The Muse",
                    "status": "failed",
                    "records": 0,
                    "finished_at": datetime.now(),
                    "error": str(e),
                }
            )

        # Remotive ingestion
        print("Ingesting from Remotive...")
        try:
            remotive_run = await service.ingest(remotive_source)
            results.append(
                {
                    "source": "remotive",
                    "name": "Remotive",
                    "status": remotive_run.status,
                    "records": remotive_run.records_received or 0,
                    "finished_at": remotive_run.finished_at or datetime.now(),
                }
            )
        except Exception as e:
            results.append(
                {
                    "source": "remotive",
                    "name": "Remotive",
                    "status": "failed",
                    "records": 0,
                    "finished_at": datetime.now(),
                    "error": str(e),
                }
            )

        # Print results
        print("\n" + "=" * 80)
        print("INGESTION RESULTS")
        print("=" * 80)
        print(f"{'Source':<15} {'Status':<10} {'Records':<10} {'Finished At':<20}")
        print("-" * 80)

        for result in results:
            status = result["status"]
            records = result["records"]
            finished_at = result["finished_at"].strftime("%Y-%m-%d %H:%M:%S")

            print(f"{result['name']:<15} {status:<10} {records:<10} {finished_at:<20}")

            if "error" in result:
                print(f"  Error: {result['error']}")

        print("=" * 80)

        # Close clients
        muse_client.close()
        await remotive_client.aclose()

    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(run_ingestion())
