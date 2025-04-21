from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.sql import expression
from app.database.model import ResourceLink
from app.database.db import get_session
from typing import Optional


router = APIRouter()

@router.get("/data")
async def get_stats_data(
    session: AsyncSession = Depends(get_session),
    status: Optional[str] = None,
    bot: Optional[str] = None,
    sort_by: str = "submitted_at",
    sort_order: str = "desc",
    limit: int = 100,
    offset: int = 0,
):
    
    query = select(ResourceLink)
    
   
    if status:
        query = query.where(ResourceLink.status == status)
    if bot:
        query = query.where(ResourceLink.bot == bot)
    
   
    if sort_order.lower() == "asc":
        query = query.order_by(getattr(ResourceLink, sort_by).asc())
    else:
        query = query.order_by(getattr(ResourceLink, sort_by).desc())
    
  
    query = query.limit(limit).offset(offset)
    
   
    results = await session.execute(query)
    links = results.scalars().all()
    
 
    count_query = select(
        ResourceLink.status,
        func.count(ResourceLink.id)
    ).group_by(ResourceLink.status)
    
    count_results = await session.execute(count_query)
    counts = {status: count for status, count in count_results.all()}
    
  
    bot_query = select(
        ResourceLink.bot,
        ResourceLink.status,
        func.count(ResourceLink.id)
    ).group_by(ResourceLink.bot, ResourceLink.status)
    
    bot_results = await session.execute(bot_query)
    bot_counts = {}
    
    for bot_name, status, count in bot_results.all():
        if bot_name not in bot_counts:
            bot_counts[bot_name] = {}
        bot_counts[bot_name][status] = count
    
  
    link_data = []
    for link in links:
        link_data.append({
            "id": str(link.id),
            "link": link.link,
            "type": link.type,
            "bot": link.bot,
            "status": link.status,
            "error_message": link.error_message,
            "submitted_at": link.submitted_at.isoformat() if link.submitted_at else None
        })
    
    return {
        "links": link_data,
        "summary": counts,
        "bot_summary": bot_counts,
        "total": sum(counts.values()),
        "filtered": len(link_data)
    }