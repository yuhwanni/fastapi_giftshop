from fastapi import APIRouter, Depends, Form
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session, get_async_gift_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, between, and_, text
from sqlalchemy.orm import selectinload

from reward_app.models.member_model import Member

from reward_app.models.giftishow_goods_model import GiftishowGoods
from reward_app.models.giftishow_send_model import GiftishowSend
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
from datetime import datetime

from reward_app.core.security import get_current_user

import json

from reward_app.service.point_service import save_point, reduce_point
from dotenv import load_dotenv
import os
import random
import httpx

from reward_app.utils.giftishow import fetch_coupon_send, fetch_coupon_info, fetch_coupon_cancel

router = APIRouter()

load_dotenv()
USER_ID = os.getenv("USER_ID", "")
SEND_NUMBER = os.getenv("SEND_NUMBER", "")

API_CODE_COUPON_SEND = os.getenv("API_CODE_COUPON_SEND", "")
AUTH_CODE = os.getenv("AUTH_CODE", "")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
DEV_YN = os.getenv("DEV_YN", "")
API_COUPON_SEND_URL = os.getenv("API_COUPON_SEND_URL", "")



@router.post("/send/proc", name="쿠폰 전송요청")
async def send_proc(    
    goods_code: str =Form(title="상품번호",description="상품번호")   
    , db: AsyncSession = Depends(get_async_session)
    , gift_db: AsyncSession = Depends(get_async_gift_session)
    , current_user = Depends(get_current_user), 
):    
    
    user_seq = current_user.get('user_seq')

    # 사용자 있는지 확인    
    result = await db.execute(select(Member).where(Member.user_seq==user_seq))
    member = result.scalar_one_or_none()
    if member is None:
        return make_resp("E900")
    if member.user_phone is None or member.user_phone == '':        
        return make_resp("E901")

    # 남은 포인트와 상품가격 비교
    point = member.user_point

    result = await gift_db.execute(select(GiftishowGoods).where(GiftishowGoods.goodsCode==goods_code))
    goods = result.scalar_one_or_none()

    if goods is None:
        return make_resp("E601")

    goods_price = int(goods.salePrice)
    goods_name = goods.goodsName

    if point < goods_price:
        return make_resp("E600")
    if goods.goodsStateCd != 'SALE':
        return make_resp("E602")
    tr_id = ''

    user_phone = member.user_phone
    user_phone = user_phone.replace('-','')

    """
    고유한 tr_id 생성
    형식: reward_YYYYMMDD_랜덤숫자
    최대 10번까지 시도
    """
    today = datetime.now().strftime("%Y%m%d")
    tr_id = False
    tr_id_gen = False
    for _ in range(10):  # 최대 10번 시도
        tr_id = f"reward_{today}_{random.randint(100000, 999999)}"

        result = await gift_db.execute(
            select(GiftishowSend).where(GiftishowSend.tr_id == tr_id)
        )
        exist = result.scalar_one_or_none()

        if not exist:
            tr_id_gen = True
            break
        
    if not tr_id_gen:
        return make_resp("E603", {"tr_id":tr_id})

    mms_msg = f"{goods_name} 상품이 도착하였습니다"    
    mms_title='상품이 도착하였습니다'
    rev_info_yn = 'N'
    gubun = 'N'

    stmt = insert(GiftishowSend).values(
        goods_code=goods_code,
        user_seq=user_seq,
        mms_msg=mms_msg,
        mms_title=mms_title,
        callback_no=SEND_NUMBER,
        phone_no=user_phone,
        tr_id=tr_id,
        rev_info_yn=rev_info_yn,
        # rev_info_date=req.rev_info_date,
        # rev_info_time=req.rev_info_time,
        # template_id=req.template_id,
        # banner_id=req.banner_id,
        user_id=USER_ID,
        gubun=gubun,
        crt_date=datetime.now()
    ).returning(GiftishowSend.order_no)
    result = await gift_db.execute(stmt)
    if not result:
        return make_resp("E604")

    order_no = result.scalar()
    await gift_db.commit()
    
    send_data = {}

    send_data = await fetch_coupon_send({
        "goods_code":goods_code,
        "mms_msg":mms_msg,
        "mms_title":mms_title,
        "phone_no":user_phone,
        "rev_info_yn":rev_info_yn,
        # "rev_info_date":rev_info_date,
        # "rev_info_time":rev_info_time,
        # "template_id":template_id,
        # "banner_id":banner_id,
        "gubun":gubun,
        "tr_id":tr_id,
        })


    # coupon_data = None
    cancel_data = None
    send_result = True
    msg = ""
    # 3. 결과 처리
    if send_data.get("code") == "0000" and send_data["result"]["code"] == "0000":
        # 쿠폰 확인 API 호출        
        # coupon_data = await fetch_coupon_info(tr_id)
        send_result = True
    else:
        # 발송 실패 - 취소 처리 요청 후 쿠폰 다시 확인
        cancel_data = await fetch_coupon_cancel(tr_id)
        # coupon_data = await fetch_coupon_info(tr_id)
        send_result = False

    # 결과값 저장
    if send_result:
        send_result = send_data.get("result",{}).get("result",{})
        upd_stmt = update(GiftishowSend).where(GiftishowSend.order_no == order_no).values(
            code=send_data.get("code"),
            message=send_data.get("message"),
            pinNo = send_result.get("pinNo") if send_result.get("pinNo") is not None else None,
            orderNo = send_result.get("orderNo") if send_result.get("orderNo") is not None else None,
            couponImgUrl = send_result.get("couponImgUrl") if send_result.get("couponImgUrl") is not None else None,
            upd_date=datetime.now()
        )
        await gift_db.execute(upd_stmt)
        await gift_db.commit()
    else:
        upd_stmt = update(GiftishowSend).where(GiftishowSend.order_no == order_no).values(
            code=send_data.get("code"),
            message=send_data.get("message"),
            cancel_code=cancel_data.get("code"),
            cancel_message=cancel_data.get("message"),
            # detail_yn="Y",
            upd_date=datetime.now()
        )
        await gift_db.execute(upd_stmt)
        await gift_db.commit()
        return make_resp("E605", {"gift_resp_code":cancel_data.get("code"),"req":send_data.get("req", {})})

    # 포인트 차감
    # send_result        
    point_result = await reduce_point(db, user_seq, f"상품구입 {goods_name}", goods_price, "API_GIFTISHOW_SEND", order_no, "G")

    if point_result:       
        await db.commit() 
        upd_stmt = update(GiftishowSend).where(GiftishowSend.order_no == order_no).values(
            is_point_reduce='Y',
            upd_date=datetime.now()
        )
        await gift_db.execute(upd_stmt)
        await gift_db.commit()

        return make_resp("S")
    else:
        return make_resp("E606")

@router.post("/cancel/proc", name="쿠폰 취소요청(임시 url 삭제할 예정)")
async def cancel_proc(    
    tr_id: str =Form(title="tr_id",description="tr_id")       
    , gift_db: AsyncSession = Depends(get_async_gift_session)
):    
    cancel_data = await fetch_coupon_cancel(tr_id)

    upd_stmt = update(GiftishowSend).where(GiftishowSend.tr_id == tr_id).values(
        detail_yn="N",
    )
    await gift_db.execute(upd_stmt)
    await gift_db.commit()