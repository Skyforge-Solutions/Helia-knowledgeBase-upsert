# app/worker.py
import asyncio, logging, uuid, os, contextlib
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import AsyncSessionLocal
from app.model import ResourceLink
from app.process import process_record

logger = logging.getLogger("poller")
POLL_INTERVAL = 15               # seconds between scans
BATCH_SIZE    = 10               # rows at a time
CONCURRENCY   = 4                # parallel tasks inside a batch

async def _next_batch(session: AsyncSession):
    """Atomically claim <=BATCH_SIZE pending rows (SKIP LOCKED)."""
    stmt = (
        select(ResourceLink)
        .where(ResourceLink.status == "pending")
        .limit(BATCH_SIZE)
        .with_for_update(skip_locked=True)
    )
    rows = (await session.execute(stmt)).scalars().all()

    # mark them as “processing” 
    if rows:
        ids = [r.id for r in rows]
        await session.execute(
            update(ResourceLink)
            .where(ResourceLink.id.in_(ids))
            .values(status="processing")
        )
        await session.commit()
    return rows

async def poll_forever():
    logger.info("background poller started")
    try:
        while True:
            async with AsyncSessionLocal() as session:
                batch = await _next_batch(session)

            if not batch:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            # bounded parallelism
            sem = asyncio.Semaphore(CONCURRENCY)
            async def _wrapped(rec):
                async with sem:
                    await process_record(rec.id)

            await asyncio.gather(*(_wrapped(r) for r in batch))
    except asyncio.CancelledError:
        logger.info("poller cancelled – shutting down")
    except Exception:            # keep the task alive on unexpected errors
        logger.exception("poller crashed; restarting in 5 s")
        await asyncio.sleep(5)
        asyncio.create_task(poll_forever())