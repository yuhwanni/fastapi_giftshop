# fetch_brand_goods_batch.py
import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv
import httpx
import uuid

import datetime
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.giftishow_send_model import GiftishowSend
from models.send_request import SendRequest

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

API_COUPON_SEND_URL = os.getenv("BIZAPI_URL", "https://bizapi.giftishow.com/bizApi/brands")+"/"+os.getenv("BIZAPI_COUPON_SEND", "send")
API_COUPON_INFO_URL = os.getenv("BIZAPI_URL", "https://bizapi.giftishow.com/bizApi/brands")+"/"+os.getenv("BIZAPI_COUPON_INFO", "coupons")
API_COUPON_CANCEL_URL = os.getenv("BIZAPI_URL", "https://bizapi.giftishow.com/bizApi/brands")+"/"+os.getenv("BIZAPI_COUPON_CANCEL", "cancel")

API_BRAND_URL = os.getenv("BIZAPI_URL", "https://bizapi.giftishow.com/bizApi/brands")+"/"+os.getenv("BIZAPI_BRAND", "brands")
API_GOODS_URL = os.getenv("BIZAPI_URL", "https://bizapi.giftishow.com/bizApi/brands")+"/"+os.getenv("BIZAPI_GOODS", "goods")

API_CODE_BRAND = os.getenv("API_CODE_BRAND", "0102")
API_CODE_GOODS = os.getenv("API_CODE_GOODS", "0101")

API_CODE_COUPON_SEND = os.getenv("API_CODE_COUPON_SEND", "0204")
API_CODE_COUPON_INFO = os.getenv("API_CODE_COUPON_INFO", "0201")
API_CODE_COUPON_CANCEL = os.getenv("API_CODE_COUPON_CANCEL", "0202")

SEND_NUMBER = os.getenv("SEND_NUMBER", "")
USER_ID = os.getenv("USER_ID", "")
 

AUTH_CODE = os.getenv("CUSTOM_AUTH_CODE")
AUTH_TOKEN = os.getenv("CUSTOM_AUTH_TOKEN")
DEV_YN = os.getenv("DEV_YN", "Y")

# 유니크 트랜잭션 ID 생성
async def generate_tr_id(db: AsyncSession) -> str:
    """
    고유한 tr_id 생성
    형식: reward_YYYYMMDD_랜덤숫자
    """
    today = datetime.datetime.now().strftime("%Y%m%d")

    while True:
        candidate = f"reward_{today}_{random.randint(100000, 999999)}"

        result = await db.execute(
            select(GiftishowSend).where(GiftishowSend.tr_id == candidate)
        )
        exists = result.scalar_one_or_none()

        if not exists:
            return candidate

def parse_end_date(date_str: str):
    if not date_str:
        return None
    try:
        # "2999-12-30T15:00:00.000+0000" -> naive datetime
        dt = datetime.datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        return dt
    except Exception as e:
        print(f"endDate 변환 실패: {date_str}, {e}")
        return None

async def fetch_brands():
    params = {
        "api_code": API_CODE_BRAND,
        "custom_auth_code": AUTH_CODE,
        "custom_auth_token": AUTH_TOKEN,
        "dev_yn": DEV_YN
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(API_BRAND_URL, data=params)
        data = resp.json()
        return data.get("result", {}).get("brandList", [])


async def fetch_goods(start=1, size=100):
    params = {
        "api_code": API_CODE_GOODS,
        "custom_auth_code": AUTH_CODE,
        "custom_auth_token": AUTH_TOKEN,
        "dev_yn": DEV_YN,
        "start": str(start),
        "size": str(size)
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(API_GOODS_URL, data=params)
        data = resp.json()
        return data.get("result", {}).get("goodsList", [])

async def fetch_coupon_send(req: Dict):
    params = {
        "api_code": API_CODE_COUPON_SEND,
        "custom_auth_code": AUTH_CODE,
        "custom_auth_token": AUTH_TOKEN,
        "dev_yn": DEV_YN,
        "callback_no":SEND_NUMBER,
        "user_id":USER_ID
    }
    # req_dic = req.model_dump()

    paylods = params | req

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(API_COUPON_SEND_URL, data=paylods)        
        data = resp.json()

        # request = client.build_request("POST", API_COUPON_SEND_URL, data=paylods)
        # print("보낼 요청:", request.method, request.url, request.headers, request.content)

        # response = await client.send(request)
        # print("응답 상태 코드:", response.status_code)
        # print("응답 헤더:", response.headers)
        # print("응답 내용:", response.text)


        return data

async def fetch_coupon_info(tr_id: str):
    params = {
        "api_code": API_CODE_COUPON_INFO,
        "custom_auth_code": AUTH_CODE,
        "custom_auth_token": AUTH_TOKEN,
        "dev_yn": DEV_YN,
        "tr_id": tr_id,
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(API_COUPON_INFO_URL, data=params)
        data = resp.json()
        return data

async def fetch_coupon_cancel(tr_id: str):
    params = {
        "api_code": API_CODE_COUPON_CANCEL,
        "custom_auth_code": AUTH_CODE,
        "custom_auth_token": AUTH_TOKEN,
        "dev_yn": DEV_YN,
        "tr_id": tr_id,
        "user_id":USER_ID
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(API_COUPON_CANCEL_URL, data=params)
        data = resp.json()
        return data