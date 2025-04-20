from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.model import ResourceLink
from app.db import get_session
import csv, uuid
from io import StringIO
from urllib.parse import urlparse

router = APIRouter()

MAX_FILE_SIZE = 5_000_000   # 5 MB
MAX_ROWS = 1000

def is_valid_link(link: str) -> bool:
    p = urlparse(link)
    return p.scheme in ("http", "https") and bool(p.netloc)

@router.post("/upload")
async def upload_links(
    file: UploadFile = File(..., max_length=MAX_FILE_SIZE),
    bot: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .csv files allowed"
        )
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Invalid file type"
        )

    contents = await file.read(MAX_FILE_SIZE + 1)
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="CSV too large (max 5 MB)"
        )

    decoded = contents.decode("utf-8", errors="ignore")
    reader = csv.reader(StringIO(decoded))

    errors = []
    seen = set()
    rows = []

    for i, row in enumerate(reader, start=1):
        if i > MAX_ROWS:
            errors.append({"row": None, "error": f"Too many rows (max {MAX_ROWS})"})
            break

        if i == 1 and row and row[0].strip().lower() == "url":
            continue

        if not row or len(row) != 1:
            errors.append({"row": i, "error": "Expected exactly one column"})
            continue

        link = row[0].strip()
        if not link:
            errors.append({"row": i, "error": "Empty link"})
            continue

        if not is_valid_link(link):
            errors.append({"row": i, "error": "Invalid URL"})
            continue

        if link[0] in ("=", "+", "-", "@"):
            link = "'" + link

        if link in seen:
            continue
        seen.add(link)
        rows.append(link)

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors, "accepted": len(rows)}
        )

    stmt = select(ResourceLink.link).where(ResourceLink.link.in_(rows))
    existing = {r[0] for r in (await session.execute(stmt)).all()}

    new_links = [l for l in rows if l not in existing]
    duplicates = len(rows) - len(new_links)

    to_insert = []
    for link in new_links:
        link_type = "pdf" if link.lower().endswith(".pdf") else "url"
        to_insert.append(ResourceLink(
            id=uuid.uuid4(),
            link=link,
            type=link_type,
            bot=bot
        ))

    if to_insert:
        session.add_all(to_insert)
        await session.commit()

    return {"status": "success", "inserted": len(to_insert), "duplicates": duplicates}