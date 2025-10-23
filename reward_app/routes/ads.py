from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy import func

from reward_app.models.help_model import Help
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
router = APIRouter()

@router.get("/callback", name="광고적립 콜백(하는중)")
async def callback(request: Request,  db: AsyncSession = Depends(get_async_session)):
    client_host = request.client.host
    