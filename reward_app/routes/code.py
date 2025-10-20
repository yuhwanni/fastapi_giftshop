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

from reward_app.core.config import make_resp, RESP_CODE
import base64

from reward_app.service.point_service import save_point



router = APIRouter()

@router.post("/list", name="코드 목록")
async def list():
# async def login(email: str =Query(title="email",description="사용자 아이디 email hong@example.com"), password: str =Query(title="password",description="비밀번호 user_password123"), db: AsyncSession = Depends(get_async_session)):
    return RESP_CODE
