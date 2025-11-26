from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.crm.service import CRMService

async def get_crm_service(
    session: Annotated[AsyncSession, Depends(get_db)]
) -> CRMService:
    """Dependency provider for CRMService."""
    return CRMService(session)