from fastapi import APIRouter, HTTPException, Depends, Query
from reward_app.core.security import create_access_token
from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func

from reward_app.models.member_model import Member
from reward_app.models.sms_history_model import SmsHistory
from reward_app.models.auth_verify_model import AuthVerify
from reward_app.models.point_history_model import PointHistory

from datetime import datetime, timedelta, UTC

import re
import httpx
import secrets
from reward_app.utils.common import generate_secure_6digit_code, is_valid_phone_number, generate_unique_referral_code, is_valid_email, is_valid_password

import os
from dotenv import load_dotenv

from reward_app.core.config import make_resp
import base64

from reward_app.service.point_service import save_point



router = APIRouter()

@router.post("/login", name="이메일 로그인")
async def login(email: str = "hong@example.com", password: str = "user_password123", db: AsyncSession = Depends(get_async_session)):
# async def login(email: str =Query(title="email",description="사용자 아이디 email hong@example.com"), password: str =Query(title="password",description="비밀번호 user_password123"), db: AsyncSession = Depends(get_async_session)):
    r = await db.execute(select(Member).where(Member.user_email==email))
    member = r.scalars().first()

    if member is None:
        return make_resp("E1")

    db_hashed = member.user_pwd

    if bcrypt.checkpw(password.encode('utf-8'), db_hashed.encode('utf-8')):        
        upd_stmt = update(Member).where(Member.user_email == email).values(
            last_login_date=datetime.now()
        )
        await db.execute(upd_stmt)
        await db.commit() 
    else:
        return make_resp("E1")
    
    token = await create_access_token({"sub": member.user_email, "user_seq": member.user_seq})
    return make_resp("S", {"access_token": token})
