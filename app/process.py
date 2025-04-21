# app/process.py
import asyncio, logging, requests
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app.model import ResourceLink
from app.pinecone import upsert_text
from app.scraper import scrape_blog, scrape_pdf

logger = logging.getLogger("processor")

async def _verify(link: str) -> None:
    loop = asyncio.get_running_loop()
    def _head():
        return requests.head(link, timeout=5)
    resp = await loop.run_in_executor(None, _head)
    if resp.status_code != 200:
        raise ValueError(f"HEAD {resp.status_code}")

async def process_record(record_id: str):
    async with AsyncSessionLocal() as session:
        rec: ResourceLink | None = await session.get(ResourceLink, record_id)
        if not rec:
            return

        try:
            # 1) URL health check
            await _verify(rec.link)

            # 2) scrape content
            text = await asyncio.to_thread(
                scrape_blog if rec.type == "url" else scrape_pdf,
                rec.link
            )
            if not text or text.startswith("Error"):
                raise ValueError(text or "No content extracted")

            # 3) embed & upsert into Pinecone
            #    we wrap in to_thread so we don't block the event loop on network calls
            await asyncio.to_thread(
                upsert_text,
                [text],
                [{"source": rec.link}],
                rec.bot
            )

            # 4) mark as completed
            rec.status = "completed"

        except Exception as e:
            # on any failure, record the error
            rec.status = "failed"
            rec.error_message = str(e)
            logger.warning("record %s failed: %s", rec.id, e)

        finally:
            await session.commit()