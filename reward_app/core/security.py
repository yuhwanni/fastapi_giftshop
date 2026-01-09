from datetime import datetime, timezone, timedelta, UTC
from jose import jwt, JWTError, ExpiredSignatureError
# from reward_app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from reward_app.core.config import make_resp
from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.models.member_model import Member


import os
from dotenv import load_dotenv
from reward_app.utils.log_util import api_logger as logger

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")

ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE_DAYS = int(REFRESH_TOKEN_EXPIRE_DAYS)

KST = timezone(timedelta(hours=9))

async def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=expires_delta)
    # exp 는 utc로 응답할때는 한국 시각으로
    kst_time = expire.astimezone(KST)
    
    to_encode.update({"exp": expire, "type": "access"})
    access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token":access_token, "access_token_expire_date": kst_time}

async def create_refresh_token(data: dict, expires_delta: int = REFRESH_TOKEN_EXPIRE_DAYS):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=expires_delta)  # ✅ UTC aware
    kst_time = expire.astimezone(KST)

    to_encode.update({"exp": expire, "type": "refresh"})
    refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return {"refresh_token": refresh_token, "refresh_token_expire_date": kst_time}

def is_token_expired(payload: dict) -> bool:
    exp = payload.get("exp")
    if not exp:
        return True  # exp 없으면 만료 처리

    now = datetime.now(timezone.utc).timestamp()
    
    return now > exp

async def verify_token_old(token: str, token_type: str = "access"):
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None

        # now = datetime.now()
        # exp = payload.get("exp")

        # expire_date = datetime.fromtimestamp(exp)


        # print('expire')
        # print(exp)
        # print(expire_date)
        # if now>expire_date:
        #     return None
        return payload
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None
    # except Exception:
    #     return None

async def verify_token(token: str, token_type: str = "access"):
    if not token:
        return None

    try:
        logger.info(f"[verify_token] raw token = {token}")
        logger.info(f"[verify_token] token_type = {token_type}")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # ✅ 여기서 exp 자동검증
        logger.info(f"[verify_token] decoded payload = {payload}")

        # ✅ 토큰 타입 검사 (access/refresh 구분)
        if payload.get("type") != token_type:
            logger.error(f"[verify_token] token type mismatch: {payload.get('type')} != {token_type}")
            return None

        return payload

    except ExpiredSignatureError as e:
        logger.error(f"[verify_token] EXPIRED token: {e}")
        return None
    except JWTError as e:
        logger.error(f"[verify_token] JWT ERROR: {e}")
        return None
    except Exception as e:
        logger.error(f"[verify_token] UNKNOWN ERROR: {e}")
        return None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    logger.info(f"[get_current_user] token = {token}")

    payload = await verify_token(token, token_type="access")
    logger.info(f"[get_current_user] payload = {payload}")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=make_resp("E500")
        )
    return payload


async def get_current_user_optional(token: str = Depends(oauth2_scheme)):        
    payload = await verify_token(token, token_type="access")
    if not payload:
        return None
    return payload
    

async def get_user_seq(current_user):
    return current_user.get('user_seq')

# async def refresh_tokens(refresh_token: str):
#     """Refresh Token Rotation: access token과 refresh token 모두 갱신"""
#     payload = await verify_token(refresh_token, token_type="refresh")
#     if not payload:
#         return make_resp("E500")
    
#     user_seq = payload.get("user_seq")
#     user_email = payload.get("sub")
    
#     # 새로운 access token과 refresh token 모두 발급
#     new_access_token = await create_access_token({"user_seq": user_seq, "sub": user_email})
#     new_refresh_token = await create_refresh_token({"user_seq": user_seq, "sub": user_email})
        
#     return {
#         "access_token": new_access_token,
#         "refresh_token": new_refresh_token,
#         "user_seq":user_seq
#     }