from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
# from reward_app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from reward_app.core.config import make_resp
from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.models.member_model import Member


import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")

ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE_DAYS = int(REFRESH_TOKEN_EXPIRE_DAYS)

async def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def create_refresh_token(data: dict, expires_delta: int = REFRESH_TOKEN_EXPIRE_DAYS):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=expires_delta)
    to_encode.update({"exp": expire, "type": "refresh"})
    refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return refresh_token

async def verify_token(token: str, token_type: str = "access"):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return make_resp("E500")
        return payload
    except JWTError:
        return None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = await verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
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