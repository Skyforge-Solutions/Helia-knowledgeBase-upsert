# app/process.py

import os, asyncio, logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import AsyncSessionLocal
from app.database.model import ResourceLink
from app.pinecone_client import upsert_text
from app.scraper import scrape_blog, scrape_pdf

logger = logging.getLogger("processor")
logger.setLevel(logging.INFO)

async def process_record(record_id: str):
    async with AsyncSessionLocal() as session:
        rec: ResourceLink | None = await session.get(ResourceLink, record_id)
        if not rec:
            logger.warning("process_record: record %s not found", record_id)
            return

        try:
            # 1) scraping
            logger.info("Record %s: scraping %s", rec.id, rec.type)
            text = await asyncio.to_thread(
                scrape_blog if rec.type == "url" else scrape_pdf,
                rec.link
            )
            logger.info("Record %s: scraped text length=%d", rec.id, len(text or ""))

            if not text or text.startswith("Error"):
                raise ValueError(f"scrape error: {text}")

            # 2) embed & upsert into Pinecone
            logger.info(
                "Record %s: embedding & upserting to Pinecone namespace=%s", 
                rec.id, rec.bot
            )
            await asyncio.to_thread(
                upsert_text,
                [text],
                [{"source": rec.link}],
                rec.bot
            )
            logger.info("Record %s: upsert complete", rec.id)

            # 3) mark as completed
            rec.status = "completed"
            logger.info("Record %s: marking completed", rec.id)

        except Exception as e:
            rec.status = "failed"
            rec.error_message = str(e)
            logger.warning("Record %s failed: %s", rec.id, e)

        finally:
            await session.commit()
            logger.info("Record %s: final status=%s", rec.id, rec.status)