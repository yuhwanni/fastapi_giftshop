from fastapi import APIRouter, HTTPException, Depends, Query
from reward_app.core.security import create_access_token, create_refresh_token, verify_token
from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, and_

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
async def login(email: str = "hong@example.com", password: str = "user_password123@", db: AsyncSession = Depends(get_async_session)):
# async def login(email: str =Query(title="email",description="사용자 아이디 email hong@example.com"), password: str =Query(title="password",description="비밀번호 user_password123"), db: AsyncSession = Depends(get_async_session)):
    r = await db.execute(select(Member).where(and_(Member.user_email==email, Member.user_stat=='Y')))
    member = r.scalars().first()

    if member is None:
        return make_resp("E1")

    db_hashed = member.user_pwd

    token = await create_access_token({"sub": member.user_email, "user_seq": member.user_seq})
    refresh_token = await create_refresh_token({"sub": member.user_email, "user_seq": member.user_seq})

    if bcrypt.checkpw(password.encode('utf-8'), db_hashed.encode('utf-8')):        
        upd_stmt = update(Member).where(Member.user_email == email).values(
            last_login_date=datetime.now(),
            refresh_token = refresh_token
        )
        await db.execute(upd_stmt)
        await db.commit() 
    else:
        return make_resp("E1")
    
    
    return make_resp("S", {"access_token": token, "refresh_token":refresh_token})
# 토큰 갱신 엔드포인트
@router.post("/refresh")
async def refresh(refresh_token: str , db: AsyncSession = Depends(get_async_session)):

    payload = await verify_token(refresh_token, token_type="refresh")
    if not payload:
        return make_resp("E500")

    user_seq = payload.get("user_seq")
    user_email = payload.get("sub")

    result = await db.execute(select(Member).where(Member.user_seq==user_seq))
    member = result.scalar_one_or_none()
    if member is None:
        return make_resp("E900")
    
    if refresh_token != member.refresh_token:
        return make_resp("E501")

    access_token = await create_access_token({"sub": user_email, "user_seq": user_seq})
    refresh_token = await create_refresh_token({"sub": user_email, "user_seq": user_seq})
        
    upd_stmt = update(Member).where(Member.user_seq == user_seq).values(
        # last_login_date=datetime.now(),
        refresh_token = refresh_token
    )
    result2 = await db.execute(upd_stmt)
    
    if not result2:
        return make_resp("E502")

    await db.commit()         

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

@router.post("/naver_login", name="네이버 로그인(개발중)")
async def naver_login(
    access_token: str =Query(description="access_token")
    , os_type: str = Query(description="os_type")
    , db: AsyncSession = Depends(get_async_session)):
    
    url = "https://openapi.naver.com/v1/nid/me"
    headers = {
        # "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {access_token}"
    }
    # payload = {"phone": "01012345678", "code": "123456"}
    payload = {}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        data = response.json()
        resultcode = data.get('resultcode')
        message = data.get('message')

        if resultcode == "00":
            user_sns_key = data.get('response').get('id')
            user_name = data.get('response').get('nickname')
            # user_sns_key = data.get('response').get('name')
            user_email = data.get('response').get('email')
            user_gender = data.get('response').get('gender')
            # user_sns_key = data.get('response').get('age')
            birthday = data.get('response').get('birthday')
            user_img = data.get('response').get('profile_image')
            birthyear = data.get('response').get('birthyear')
            user_phone = data.get('response').get('mobile')

            user_birth = birthyear+'-'+birthday

            return make_resp("S")
        else:
            return make_resp("E50",{"msg":message, "naverResultCode":resultcode})        

    return make_resp("E1001")            

@router.post("/kakao_login", name="카카오 로그인(개발중)")
async def kakao_login(
    access_token: str =Query(description="access_token")
    , os_type: str = Query(description="os_type")
    , db: AsyncSession = Depends(get_async_session)):
    
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "Authorization": f"Bearer {access_token}"
    }
    # payload = {"phone": "01012345678", "code": "123456"}
    payload = {"secure_resource":True}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        status_code = response.status_code
        data = response.json()
        
        resultcode = data.get('code')
        message = data.get('msg')

        if status_code == 200:            
            # 기본 정보
            id = data.get('id')  # Long 회원번호 필수 X
            connected_at = data.get('connected_at')  # Datetime 서비스 연결 완료 시각 필수 X

            # 프로필 동의 관련
            profile_needs_agreement = data.get('kakao_account', {}).get('profile_needs_agreement')  # Boolean 사용자 동의 시 프로필 정보(닉네임/프로필 사진) 제공 가능 필수 X
            profile_nickname_needs_agreement = data.get('kakao_account', {}).get('profile_nickname_needs_agreement')  # Boolean 사용자 동의 시 닉네임 제공 가능 필수 X
            profile_image_needs_agreement = data.get('kakao_account', {}).get('profile_image_needs_agreement')  # Boolean 사용자 동의 시 프로필 사진 제공 가능 필수 X

            # 프로필 정보
            nickname = data.get('kakao_account', {}).get('profile', {}).get('nickname')  # String 닉네임 필수 X
            profile_image_url = data.get('kakao_account', {}).get('profile', {}).get('profile_image_url')  # String 프로필 이미지 URL, 640x640 필수 X
            thumbnail_image_url = data.get('kakao_account', {}).get('profile', {}).get('thumbnail_image_url')  # String 프로필 미리보기 이미지 URL, 110x110 필수 X
            is_default_image = data.get('kakao_account', {}).get('profile', {}).get('is_default_image')  # Boolean 기본 이미지 여부 필수 X
            is_default_nickname = data.get('kakao_account', {}).get('profile', {}).get('is_default_nickname')  # Boolean 닉네임이 기본 닉네임인지 여부 X

            # 이름
            name_needs_agreement = data.get('kakao_account', {}).get('name_needs_agreement')  # Boolean 사용자 동의 시 카카오계정 이름 제공 가능 필수 X
            name = data.get('kakao_account', {}).get('name')  # String 카카오계정 이름 필수 X

            # 이메일
            email_needs_agreement = data.get('kakao_account', {}).get('email_needs_agreement')  # Boolean 사용자 동의 시 카카오계정 대표 이메일 제공 가능 필수 X
            is_email_valid = data.get('kakao_account', {}).get('is_email_valid')  # Boolean 이메일 유효 여부 필수 X
            is_email_verified = data.get('kakao_account', {}).get('is_email_verified')  # Boolean 이메일 인증 여부 필수 X
            email = data.get('kakao_account', {}).get('email')  # String 카카오계정 대표 이메일 필수 X

            # 연령대
            age_range_needs_agreement = data.get('kakao_account', {}).get('age_range_needs_agreement')  # Boolean 사용자 동의 시 연령대 제공 가능 필수 X
            age_range = data.get('kakao_account', {}).get('age_range')  # String 연령대 (1~9, 10~14, 15~19, 20~29, 30~39, 40~49, 50~59, 60~69, 70~79, 80~89, 90~) 필수 X

            # 출생 연도
            birthyear_needs_agreement = data.get('kakao_account', {}).get('birthyear_needs_agreement')  # Boolean 사용자 동의 시 출생 연도 제공 가능 필수 X
            birthyear = data.get('kakao_account', {}).get('birthyear')  # String 출생 연도 (YYYY 형식) 필수 X

            # 생일
            birthday_needs_agreement = data.get('kakao_account', {}).get('birthday_needs_agreement')  # Boolean 사용자 동의 시 생일 제공 가능 필수 X
            birthday = data.get('kakao_account', {}).get('birthday')  # String 생일 (MMDD 형식) 필수 X
            birthday_type = data.get('kakao_account', {}).get('birthday_type')  # String 생일 타입 (SOLAR: 양력, LUNAR: 음력) 필수 X
            is_leap_month = data.get('kakao_account', {}).get('is_leap_month')  # Boolean 생일의 윤달 여부 필수 X

            # 성별
            gender_needs_agreement = data.get('kakao_account', {}).get('gender_needs_agreement')  # Boolean 사용자 동의 시 성별 제공 가능 필수 X
            gender = data.get('kakao_account', {}).get('gender')  # String 성별 (female: 여성, male: 남성) 필수 X

            # 전화번호
            phone_number_needs_agreement = data.get('kakao_account', {}).get('phone_number_needs_agreement')  # Boolean 사용자 동의 시 전화번호 제공 가능 필수 X
            phone_number = data.get('kakao_account', {}).get('phone_number')  # String 카카오계정의 전화번호 (+82 00-0000-0000 형식) 필수 X

            # CI (연계정보)
            ci_needs_agreement = data.get('kakao_account', {}).get('ci_needs_agreement')  # Boolean 사용자 동의 시 CI 참고 가능 필수 X
            ci = data.get('kakao_account', {}).get('ci')  # String 연계정보 필수 X
            ci_authenticated_at = data.get('kakao_account', {}).get('ci_authenticated_at')  # Datetime CI 발급 시각, UTC 필수 X

            user_sns_key = id           
            user_name = nickname            
            user_email = email
            user_gender = gender
            birthday = birthday
            user_img = thumbnail_image_url
            birthyear = birthyear
            user_phone = phone_number
            user_birth = birthyear.zfill(4)+'-'+birthday

            member = Member
            member.user_sns_key = user_sns_key
            member.user_name = user_name
            member.user_email = user_email
            member.user_gender = user_gender
            member.user_img = user_img
            member.user_phone = user_phone
            member.user_birth = user_birth
            member.os_type = os_type
            member.user_sns_type = 'K'

            return make_resp("S")
        else:
            return make_resp("E50",{"msg":message, "kakaoResultCode":resultcode})        

    return make_resp("E1001")

    async def sns_login(member: Member):
        print('hi')