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

from reward_app.utils.params import AgreementYn, GenderType, OsType


router = APIRouter()

# 회원가입 페이지 진입시 호출
@router.post("/token", name="회원가입, 아이디찾기,비밀번호 찾기 전 호출하여 토큰 저장")
async def token(device_id: str =Query(title="device_id",description="기기값"), db: AsyncSession = Depends(get_async_session)):
    auth_token = ""
    while True:
        auth_token = secrets.token_urlsafe(32)

        stmt = select(AuthVerify).where(AuthVerify.auth_token==auth_token)
        total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
        total_count = total_results.scalar() or 0

        if total_count == 0:
            stmt = insert(AuthVerify).values(
                auth_token=auth_token,
                device_id=device_id
            )
            await db.execute(stmt)            
            await db.commit()
            break
    
    return make_resp("S", {"auth_token": auth_token})

@router.post("/join_check", name="이메일, 비밀번호 체크")
async def join_check(auth_token: str =Query(title="auth_token",description="auth_token")
, email: str =Query(title="email",description="이메일")
, pwd: str =Query(title="pwd",description="비밀번호")
, re_pwd: str =Query(title="re_pwd",description="비밀번호")
, terms_yn: AgreementYn =Query(title="terms_yn",description="이용약관 동의")
, privacy_yn: AgreementYn =Query(title="privacy_yn",description="개인정보 수집 동의")
, db: AsyncSession = Depends(get_async_session)):    
    stmt = select(AuthVerify).where(AuthVerify.auth_token==auth_token)

    r = await db.execute(stmt)
    auth_verify = r.scalars().first()

    if auth_verify is None:
        return make_resp("E2")
    
    if not is_valid_email(email):
        return make_resp("E13")

    if not is_valid_password(pwd):
        return make_resp("E15")
    if pwd != re_pwd:
        return make_resp("E14")
    
    if terms_yn != "Y":
        return make_resp("E30")
    if privacy_yn != "Y":
        return make_resp("E31")        

    stmt = select(Member).where(Member.user_email==email)
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0

    if total_count >0:
        return make_resp("E8")
    
    return make_resp("S")

# 문자 전송 
@router.post("/send_sms", name="문자 보내기")
async def send_sms(auth_token: str =Query(title="auth_token",description="auth_token"), phone: str =Query(title="phone",description="휴대폰 번호")
    , db: AsyncSession = Depends(get_async_session)):
    stmt = select(AuthVerify).where(AuthVerify.auth_token==auth_token)

    r = await db.execute(stmt)
    auth_verify = r.scalars().first()

    if auth_verify is None:
        return make_resp("E2")
    
    phone = re.sub(r'[^0-9]', '', phone)
    
    if is_valid_phone_number(phone) == False:
        return make_resp("E3")

    load_dotenv()

    SMS_EXPIRE_MIN = os.getenv("SMS_EXPIRE_MIN")
    BIZPURIO_ID = os.getenv("BIZPURIO_ID")
    BIZPURIO_PWD = os.getenv("BIZPURIO_PWD")
    BIZPURIO_TOKEN_URL = os.getenv("BIZPURIO_TOKEN_URL")
    BIZPURIO_SEND_URL = os.getenv("BIZPURIO_SEND_URL")
    BIZPURIO_FROM_NUMBER = os.getenv("BIZPURIO_FROM_NUMBER")
    
    verify_code = generate_secure_6digit_code()
    expire_date = datetime.now() + timedelta(minutes=int(SMS_EXPIRE_MIN))
    msg = f"인증 코드는 [{verify_code}] 입니다"

    stmt = insert(SmsHistory).values(
        receive_number=phone,
        send_number=BIZPURIO_FROM_NUMBER,
        subject="",
        message=msg
    ).returning(SmsHistory.sms_seq)
    result = await db.execute(stmt)
    sms_seq = result.scalar()
    await db.commit()

    auth_str = f"{BIZPURIO_ID}:{BIZPURIO_PWD}"
    auth_bytes = auth_str.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    url = BIZPURIO_TOKEN_URL
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {auth_base64}"
    }
    # payload = {"phone": "01012345678", "code": "123456"}
    payload = {}
    bizpurio_accesstoken = ""
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        data = response.json()
        bizpurio_accesstoken = data.get('accesstoken')
    
    url = BIZPURIO_SEND_URL
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {bizpurio_accesstoken}"
    }
    payload = {
        "account":BIZPURIO_ID,
        "type": "sms",        
        "from": BIZPURIO_FROM_NUMBER,        
        "to": phone,        
        # "country": "",        
        "content": {
            "sms": {
                "message": msg
            }
        },        
        "refkey": f"-sms_seq",        
        # "userinfo": "",        
        # "resend": "",        
        # "recontent": "",        
        # "resellercode": "",        
        # "sendtime" : ""
    }
    
    send_result_data= {}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)    
        send_result_data = response.json()
    if send_result_data is not None:
        result_code = send_result_data.get('code')
        result_description = send_result_data.get('description')
        result_messagekey = send_result_data.get('messagekey')
    
    stmt = update(SmsHistory).where(SmsHistory.sms_seq==sms_seq).values(
        result_code=result_code,
        result_description=result_description,
        result_messagekey=result_messagekey,
    )
    await db.execute(stmt)    
    await db.commit()

    stmt = update(AuthVerify).where(AuthVerify.auth_token == auth_token).values(
        phone=phone,
        verify_code=verify_code,
        expire_date = expire_date
    )
    await db.execute(stmt)            
    await db.commit()
    
    if result_code == 1000:
        return make_resp("S", {"인증번호(임시로 보여짐)":verify_code})
    else:
        return make_resp("E4", {"문자전송 실패 인증번호(임시로 보여짐)":verify_code, "result_code":result_code})    

    

@router.post("/auth_sms", name="인증번호 확인")
async def auth_sms(auth_token: str =Query(title="auth_token",description="auth_token")
    , verify_code: str =Query(title="verify_code",description="인증 번호")
    , email: str =Query(default=None, title="email",description="비밀번호 변경 인증시 필수")
    , db: AsyncSession = Depends(get_async_session)):
    verify_result = False
    msg = ""
    stmt = select(AuthVerify).where(AuthVerify.auth_token==auth_token)

    r = await db.execute(stmt)
    auth_verify = r.scalars().first()

    if auth_verify is None:
        return make_resp("E2")    
    if auth_verify.expire_date < datetime.now():        
        return make_resp("E5")

    if auth_verify.verify_yn == "Y":        
        return make_resp("E6")

    if auth_verify.verify_code == verify_code:        
        stmt = update(AuthVerify).where(AuthVerify.auth_token == auth_token).values(
            verify_yn='Y',
            verify_date = datetime.now(),
            user_email = email
        )
        await db.execute(stmt)            
        await db.commit()
        return make_resp("S")
    else :
        return make_resp("E6")



# 회원가입
@router.post("/join", name="회원가입")
async def join(auth_token: str =Query(title="auth_token",description="auth_token")
, email: str =Query(title="email",description="이메일")
, pwd: str =Query(title="pwd",description="비밀번호")
, re_pwd: str =Query(title="re_pwd",description="비밀번호")
, nickname: str =Query(title="nickname",description="닉네임")
, gender: GenderType =Query(default="U", title="gender",description="성별 F:여성,M:남성, U:확인불가")
, birth_year: str =Query(default=None, title="birth_year",description="출생년도")
, location: str =Query(default=None, title="location",description="지역")
, referral_code: str =Query(default=None, title="referral_code",description="추천인코드")
, marketing_yn: AgreementYn =Query(default=None, title="marketing_yn",description="마케팅 정보 수신 동의")
, token: str =Query(default=None, title="token",description="푸쉬 토큰")
, device_id: str =Query(default=None, title="token",description="device id")
, os_type: OsType =Query(default='E', title="os_type",description="기기 os, A: 안드로이드, I:IOS, W:WEB, E:기타")
, db: AsyncSession = Depends(get_async_session)):    
    stmt = select(AuthVerify).where(AuthVerify.auth_token==auth_token)

    r = await db.execute(stmt)
    auth_verify = r.scalars().first()

    if auth_verify is None:
        return make_resp("E2")
    if auth_verify.verify_yn == "N":
        return make_resp("E7")
    
    if not is_valid_email(email):
        return make_resp("E13")

    if not is_valid_password(pwd):
        return make_resp("E15")
    if pwd != re_pwd:
        return make_resp("E14")

    stmt = select(Member).where(Member.user_email==email)
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0

    if total_count >0:
        return make_resp("E8")

    if gender not in ("F", "M", "U"):
        return make_resp("E16")

    if len(nickname)<2:
        return make_resp("E17")

    current_year = datetime.now().year
    max_year = current_year

    if birth_year is not None and birth_year != "" and not birth_year.isdigit():
        return make_resp("E18")
    if birth_year is not None and birth_year != "" and len(birth_year) !=4:
        return make_resp("E19")
    if birth_year is not None and birth_year != "" and len(birth_year) ==4 and int(birth_year)>max_year:
        return make_resp("E20" , {"msg":f"{max_year} 까지만 입력가능"})
    user_birth = "0000-00-00"
    if birth_year is not None and birth_year != "":
        user_birth = birth_year+"-00-00"
    password_bytes = pwd.encode('utf-8')
    # 2. 해시 생성 (salt 포함)
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    # 3. DB에 저장 (바이트 그대로 저장 가능, 또는 문자열로)
    hashed_password_str = hashed_password.decode('utf-8')
    gen_referral_code = await generate_unique_referral_code(db)
    stmt = insert(Member).values(
        user_email=email,
        user_pwd=hashed_password_str,
        user_pwd2=pwd,
        user_name=nickname,
        user_gender=gender,
        user_birth=user_birth,
        user_location=location,
        referral_code=gen_referral_code,
        user_token=token,
        marketing_yn=marketing_yn,
        marketing_date=datetime.now(),
        device_id=device_id,
        os_type=os_type
    ).returning(Member.user_seq)
    result = await db.execute(stmt)
    user_seq = result.scalar()

    load_dotenv()
    JOIN_POINT = int(os.getenv("JOIN_POINT"))
    REFERRAL_POINT = int(os.getenv("REFERRAL_POINT"))
    
    result2 = await save_point(db, user_seq, "회원가입 포인트 적립", JOIN_POINT, "PC_MEMBER", {"user_seq": user_seq}, "J")

    # 추천인 코드 있을 경우 포인트 지급
    if referral_code is not None and referral_code != "":
        
        # REFERRAL_JOIN_AD_POINT = int(os.getenv("REFERRAL_JOIN_AD_POINT"))

        stmt = select(Member).where(Member.referral_code == referral_code)
        result = await db.execute(stmt)
        re_member = result.scalars().first()
        
        if re_member is not None:
            result3 = await save_point(db, re_member.user_seq, "추천 포인트 적립", REFERRAL_POINT, "PC_MEMBER", {"user_seq": user_seq}, "I")

    stmt = delete(AuthVerify).where(AuthVerify.auth_token==auth_token)
    await db.execute(stmt)
    
    if user_seq is not None:
        await db.commit()
        return make_resp("S")
    else:
        await db.rollback()
        return make_resp("E9")

@router.post("/find_id", name="아이디 찾기")
async def find_id(auth_token: str =Query(title="auth_token",description="auth_token"), db: AsyncSession = Depends(get_async_session)):    
    join_result = False

    stmt = select(AuthVerify).where(AuthVerify.auth_token==auth_token)

    r = await db.execute(stmt)
    auth_verify = r.scalars().first()

    if auth_verify is None:
        return make_resp("E2")
    if auth_verify.verify_yn == "N":
        return make_resp("E7")


    r = await db.execute(select(Member).where(Member.user_phone==auth_verify.phone))
    member = r.scalars().first()

    if member is None:
        return make_resp("E10")
    else:
        stmt = delete(AuthVerify).where(AuthVerify.auth_token==auth_token)
        await db.execute(stmt)
        await db.commit()
        return make_resp("S", {"email":member.user_email})

@router.post("/find_email", name="이메일이 존재 하는지 확인")
async def find_email(
    auth_token: str =Query(title="auth_token",description="auth_token")
    , email: str =Query(title="email",description="email")    
    , db: AsyncSession = Depends(get_async_session)):    
    stmt = select(AuthVerify).where(AuthVerify.auth_token==auth_token)

    r = await db.execute(stmt)
    auth_verify = r.scalars().first()

    if auth_verify is None:
        return make_resp("E2")

    stmt = select(Member).where(Member.user_email==email)
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0

    if total_count == 0:
        return make_resp("E12")
    else:
        return make_resp("S", {"msg":"이메일 존재"})

@router.post("/change_pwd", name="비밀번호 변경")
async def change_pwd(
    auth_token: str =Query(title="auth_token",description="auth_token")
    , email: str =Query(title="email",description="email")
    , pwd: str =Query(title="pwd",description="pwd")
    , db: AsyncSession = Depends(get_async_session)):    
    join_result = False

    stmt = select(AuthVerify).where(AuthVerify.auth_token==auth_token)

    r = await db.execute(stmt)
    auth_verify = r.scalars().first()

    if auth_verify is None:
        return make_resp("E2")
    if auth_verify.verify_yn == "N":
        return make_resp("E7")


    password_bytes = pwd.encode('utf-8')

    # 2. 해시 생성 (salt 포함)
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    # 3. DB에 저장 (바이트 그대로 저장 가능, 또는 문자열로)
    hashed_password_str = hashed_password.decode('utf-8')

    stmt = update(Member).where(Member.user_email==auth_verify.user_email).values(        
        user_pwd=hashed_password_str,
        user_pwd2=pwd,
    )
    result = await db.execute(stmt)
    
    if result is not None:
        stmt = delete(AuthVerify).where(AuthVerify.auth_token==auth_token)
        await db.execute(stmt)
        await db.commit()
        return make_resp("S")
    else:
        return make_resp("E11")