from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, between, and_, text
from sqlalchemy.orm import selectinload

from reward_app.models.member_model import Member
from reward_app.models.point_history_model import PointHistory
from reward_app.models.quiz_model import Quiz, QuizJoin
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
from datetime import datetime

from reward_app.core.security import get_current_user

import json

router = APIRouter()


@router.get("/list", name="퀴즈 정답 제출")
async def quiz_answer(
    ym: str =Query(title="퀴즈 번호",description="년월(Y-m)")
    , db: AsyncSession = Depends(get_async_session)
    # , current_user = Depends(get_current_user), 
):
    print('hi')
    # user_seq = current_user.get('user_seq')

    