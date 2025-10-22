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

from reward_app.service.point_service import save_point

from reward_app.utils.common import generate_secure_6digit_code, is_valid_phone_number, generate_unique_referral_code, is_valid_email, is_valid_password

from reward_app.utils.params import AgreementYn, GenderType

router = APIRouter()

@router.get("/info", name="내정보")
async def list(
    db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    
    user_seq = current_user.get('user_seq')

    r = await db.execute(select(
        # Member.user_seq,             # 회원 고유번호 (PK, AUTO_INCREMENT)
        Member.user_email,           # 사용자 이메일 (로그인 ID, 고유값)
        # Member.user_sns_key,         # SNS 고유 키 (SNS 로그인 시 사용)
        # Member.user_pwd,             # 사용자 비밀번호 (암호화 저장)
        # Member.user_pwd2,            # 임시 비밀번호 (비밀번호 변경용)
        Member.user_name,            # 사용자 이름
        Member.nickname,             # 닉네임 (표시용 이름)
        Member.user_phone,           # 전화번호
        Member.user_gender,          # 성별 (F:여성, M:남성, U:미확인)
        Member.user_birth,           # 생년월일 (YYYY-MM-DD)
        Member.solar_lunar,          # 생일 구분 (S:양력, L:음력, N:선택안함)
        Member.time_of_birth,        # 태어난 시각 (HH:MM)
        Member.user_location,        # 지역 정보 (선택 입력)
        # Member.user_token,           # 푸시 토큰 (알림용)
        Member.device_id,            # 디바이스 ID (기기 식별)
        Member.user_point,           # 보유 포인트
        Member.referral_code,        # 추천인 코드
        Member.user_stat,            # 회원 상태 (Y:활성, N:중지)
        Member.user_sns_type,        # 가입 유형 (NS:일반, G:구글, N:네이버, K:카카오)
        Member.user_img,             # 프로필 이미지 URL
        Member.last_login_date,      # 마지막 로그인 일자
        Member.push_status,          # 푸시 알림 동의 여부 (Y/N)
        Member.push_date,            # 푸시 설정 등록/수정일
        # Member.terms_yn,             # 이용약관 동의 여부
        # Member.privacy_yn,           # 개인정보 수집 이용 동의 여부
        Member.marketing_yn,         # 마케팅 수신 동의 여부
        # Member.crt_date,             # 생성일자
        # Member.crt_id,               # 생성자 ID
        # Member.upd_date,             # 수정일자
        # Member.upd_id,               # 수정자 ID
        # Member.del_date              # 탈퇴일자        
    ).where(Member.user_seq==user_seq))
    
    # member = r.scalars().first()
    member = (r.mappings().first())
    return make_resp("S",{"data":member})


@router.get("/info_update/proc", name="계정정보 변경")
async def info_update_proc(
    gender: GenderType =Query(default='U', title="gender",description="성별 F:여성,M:남성, U:확인불가")
    , birth_year: str =Query(default=None, title="birth_year",description="출생년도")
    , birth_month: str =Query(default=None, title="birth_month",description="출생월")    
    , birth_day: str =Query(default=None, title="birth_day",description="출생일")    
    , location: str =Query(default="", title="location",description="지역")
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    user_seq = current_user.get('user_seq')

    if gender not in ("F", "M", "U"):
        return make_resp("E16")

    current_year = datetime.now().year
    max_year = current_year

    if birth_year is not None and not birth_year.isdigit():
        return make_resp("E18")
    if birth_year is not None and len(birth_year) !=4:
        return make_resp("E19")
    if birth_year is not None and len(birth_year) ==4 and int(birth_year)>max_year:
        return make_resp("E20" , {"msg":f"{max_year} 까지만 입력가능"})

    if birth_month is not None and not birth_month.isdigit():
        return make_resp("E66")        
    if birth_month is not None and int(birth_month) not in range(1,12) :
        return make_resp("E66")

    if birth_day is not None and not birth_day.isdigit():
        return make_resp("E67")
    if birth_day is not None and int(birth_day) not in range(1,31) :
        return make_resp("E67")

    if birth_year is None:
        birth_year = ""
    if birth_month is None:
        birth_month = ""
    if birth_day is None:
        birth_day = ""

    user_birth= birth_year.zfill(4)+"-"+birth_month.zfill(2)+"-"+birth_day.zfill(2)       

    stmt = update(Member).where(Member.user_seq==user_seq).values(
        user_gender=gender,
        user_birth=user_birth,
        user_location=location,
    )
    # print(stmt.subquery())
    result = await db.execute(stmt)
    await db.commit()
    if result:
        return make_resp("S")
    else:
        return make_resp("E60")


@router.get("/pwd_update/proc", name="비밀번호 변경")
async def pwd_update_proc(
    cur_pwd: str =Query(title="pwd",description="현재 비밀번호")
    , pwd: str =Query(title="pwd",description="변경 비밀번호")
    , re_pwd: str =Query(title="re_pwd",description="변경 비밀번호 확인")
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    user_seq = current_user.get('user_seq')

    # 기존 비밀번호 맞는지 확인
    r = await db.execute(select(Member).where(Member.user_seq==user_seq))
    member = r.scalars().first()

    if member is None:
        return make_resp("E100")

    db_hashed = member.user_pwd

    if not bcrypt.checkpw(cur_pwd.encode('utf-8'), db_hashed.encode('utf-8')):        
        return make_resp("E61")

    if not is_valid_password(pwd):
        return make_resp("E15")
    if pwd != re_pwd:
        return make_resp("E14")

    # 기존 비밀번호와 같음
    if bcrypt.checkpw(pwd.encode('utf-8'), db_hashed.encode('utf-8')):        
        return make_resp("E63")

    password_bytes = pwd.encode('utf-8')
    # 2. 해시 생성 (salt 포함)
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    # 3. DB에 저장 (바이트 그대로 저장 가능, 또는 문자열로)
    hashed_password_str = hashed_password.decode('utf-8')

    stmt = update(Member).where(Member.user_seq==user_seq).values(
        user_pwd=hashed_password_str,
        user_pwd2=pwd
    )
    result = await db.execute(stmt)
    await db.commit()
    if result:
        return make_resp("S")
    else:
        return make_resp("E60")

@router.get("/del/proc", name="회원탈퇴")
async def pwd_update_proc(
    agree_yn: AgreementYn =Query(title="pwd",description="탈퇴 동의")
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    user_seq = current_user.get('user_seq')

    if agree_yn !="Y":
        return make_resp("E64")
    # 기존 비밀번호 맞는지 확인
    

    stmt = update(Member).where(Member.user_seq==user_seq).values(
        user_stat='N',
        del_date=datetime.now()
    )
    result = await db.execute(stmt)
    await db.commit()
    if result:
        return make_resp("S")
    else:
        return make_resp("E65")
