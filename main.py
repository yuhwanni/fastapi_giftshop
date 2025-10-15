import os

from fastapi import FastAPI, Header, Depends, Query, Response, Request
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import APIKey
from fastapi.openapi.utils import get_openapi
from sqlalchemy.ext.asyncio import AsyncSession
from database.db_core import AsyncDatabase, async_db, get_async_db, get_async_session

from sqlalchemy import select
from sqlalchemy import insert
from sqlalchemy import update
from models.brand_model import Brand
from models.giftishow_send_model import GiftishowSend
from models.goods_model import Goods
from dependencies.ext_auth import verify_ext_access
from sqlalchemy.ext.asyncio import AsyncSession

from models.send_request import SendRequest
from datetime import datetime

from utils.giftishow import fetch_brands, fetch_coupon_cancel, fetch_coupon_info, fetch_coupon_send, fetch_goods, generate_tr_id, parse_end_date
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from asyncio import run
import logging
from utils.log_util import logger
from starlette.background import BackgroundTask
from starlette.types import Message

from sqlalchemy import func
from utils.common import make_page_info


load_dotenv()
USER_ID = os.getenv("USER_ID", "")
SEND_NUMBER = os.getenv("SEND_NUMBER", "")

scheduler = BackgroundScheduler()
 
JOB_ING_BRANDS = False
JOB_ING_GOODS = False
JOB_ING_SEND = False

JOB_BRANDS_SEC = int(os.getenv("JOB_BRANDS_SEC", 1800))
JOB_GOODS_SEC = int(os.getenv("JOB_GOODS_SEC", 1800))
JOB_SENDS_SEC = int(os.getenv("JOB_SENDS_SEC", 10))

async def jobBrands():
    global JOB_ING_BRANDS
    if JOB_ING_BRANDS:
        print('다른거 동작중 brand')
        return
    JOB_ING_BRANDS = True        
    
    db = AsyncDatabase()

    brands = await fetch_brands()
    success, fail = 0, []
    db_data = []

    for b in brands:
        db_data.append({
            "brandSeq": str(b.get("brandSeq")) if b.get("brandSeq") else None,
            "brandCode": b.get("brandCode"),
            "brandName": b.get("brandName"),
            "brandBannerImg": b.get("brandBannerImg"),
            "brandIconImg": b.get("brandIConImg") or b.get("brandIconImg"),
            "mmsThumImg": b.get("mmsThumImg"),
            "content": b.get("content"),
            "category1Name": b.get("category1Name"),
            "category1Seq": str(b.get("category1Seq")) if b.get("category1Seq") else None,
            "category2Name": b.get("category2Name"),
            "category2Seq": str(b.get("category2Seq")) if b.get("category2Seq") else None,
            "sort": str(b.get("sort")) if b.get("sort") else None,
            "upd_date":datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    try:
        await db.insert_many("API_GIFTISHOW_BRANDS", db_data, update_on_duplicate=True)
        success = len(db_data)
    except Exception as e:
        logger.exception(f"Brand insert/update 실패: {e}")
        fail = [b["brandCode"] for b in db_data]
    logger.info(f"fetch brands. success:{success}, fail:{len(fail)}")
    JOB_ING_BRANDS = False
    await db.engine.dispose()

async def jobGoods():
    global JOB_ING_GOODS  
    if JOB_ING_GOODS:
        print('다른거 동작중 goods')
        return
    JOB_ING_GOODS = True
    
    db = AsyncDatabase()
    start, size = 1, 100
    success_count, fail = 0, []
    while True:
        goods = await fetch_goods(start=start, size=size)
        if not goods:
            break

        db_data = []
        for g in goods:
            db_data.append({
                "goodsCode": g.get("goodsCode"),
                "goodsNo": str(g.get("goodsNo")) if g.get("goodsNo") else None,
                "goodsName": g.get("goodsName"),
                "brandCode": g.get("brandCode"),
                "brandName": g.get("brandName"),
                "content": g.get("content"),
                "contentAddDesc": g.get("contentAddDesc"),
                "discountRate": str(g.get("discountRate")) if g.get("discountRate") is not None else None,
                "goodstypeNm": g.get("goodsTypeNm"),
                "goodsImgS": g.get("goodsImgS"),
                "goodsImgB": g.get("goodsImgB"),
                "goodsDescImgWeb": g.get("goodsDescImgWeb"),
                "brandIconImg": g.get("brandIconImg"),
                "mmsGoodsImg": g.get("mmsGoodsImg"),
                "discountPrice": str(g.get("discountPrice")) if g.get("discountPrice") is not None else None,
                "realPrice": str(g.get("realPrice")) if g.get("realPrice") is not None else None,
                "salePrice": str(g.get("salePrice")) if g.get("salePrice") is not None else None,
                "srchKeyword": g.get("srchKeyword"),
                "validPrdTypeCd": g.get("validPrdTypeCd"),
                "limitday": str(g.get("limitDay")) if g.get("limitDay") else None,
                "validPrdDay": g.get("validPrdDay"),
                "endDate": parse_end_date(g.get("endDate")),
                "goodsComId": g.get("goodsComId"),
                "goodsComName": g.get("goodsComName"),
                "affiliateId": g.get("affliateId") or g.get("affiliate"),
                "affilate": g.get("affiliate"),
                "exhGenderCd": g.get("exhGenderCd"),
                "exhAgeCd": g.get("exhAgeCd"),
                "mmsReserveFlag": g.get("mmsReserveFlag"),
                "goodsStateCd": g.get("goodsStateCd"),
                "mmsBarcdCreateYn": g.get("mmsBarcdCreateYn"),
                "rmCntFlag": g.get("rmCntFlag"),
                "saleDateFlagCd": g.get("saleDateFlagCd"),
                "goodsTypeDtlNm": g.get("goodsTypeDtlNm"),
                "category1Seq": str(g.get("category1Seq")) if g.get("category1Seq") else None,
                "saleDateFlag": g.get("saleDateFlag"),
                "sellDisRate": str(g.get("sellDisRate")) if g.get("sellDisRate") is not None else None,
                "rmIdBuyCntFlagCd": g.get("rmIdBuyCntFlagCd"),
                "upd_date":datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # "point_multi": str(g.get("point_multi") or "4.4"),
                # "real_point": g.get("real_point"),
                # "bylot_yn": g.get("bylot_yn", "N"),
                # "bylot_point": str(g.get("bylot_point") or "91"),
                # "bylot_type": g.get("bylot_type", "bylot_percent"),
                # "bylot_percent": str(g.get("bylot_percent") or "0.002"),
                # "bylot_n": str(g.get("bylot_n") or "2000"),
                # "is_sale": g.get("is_sale", "N"),
                # "is_naverpay": g.get("is_naverpay", "N")
            })

        try:
            await db.insert_many("API_GIFTISHOW_GOODS", db_data, update_on_duplicate=True)
            success_count += len(db_data)
        except Exception as e:
            logger.exception(f"Goods insert/update 실패: {e}")
            fail.extend([g["goodsCode"] for g in db_data])

        start = start + 1
    logger.info(f"fetch goods. success:{success_count}, fail:{len(fail)}")
    JOB_ING_GOODS = False
    await db.engine.dispose()

async def jobSends():
    global JOB_ING_SEND
    if JOB_ING_SEND:
        print('다른거 동작중 sends')
        return
    JOB_ING_SEND = True        
    
    db = AsyncDatabase()

    success_count, fail = 0, []
    qry = """
        select tr_id from API_GIFTISHOW_SEND where detail_yn = 'N'
    """

    list = await db.fetchall(qry,{})
    logger.info(f"send count: {len(list)}")
    for row in list:
        try:
            tr_id = row["tr_id"]
            coupon_data = await fetch_coupon_info(tr_id)

            if coupon_data is not None and coupon_data.get("code") == "0000":

                coupon_info = coupon_data["result"][0]["couponInfoList"][0]

                update_qry = """
                    update API_GIFTISHOW_SEND set
                    brandNm       = :brandNm,
                    cnsmPriceAmt  = :cnsmPriceAmt,
                    correcDtm     = :correcDtm,
                    goodsCd       = :goodsCd,
                    goodsNm       = :goodsNm,
                    mmsBrandThumImg = :mmsBrandThumImg,
                    recverTelNo   = :recverTelNo,
                    sellPriceAmt  = :sellPriceAmt,
                    sendBasicCd   = :sendBasicCd,
                    sendRstCd     = :sendRstCd,
                    sendRstMsg    = :sendRstMsg,
                    sendStatusCd  = :sendStatusCd,
                    senderTelNo   = :senderTelNo,
                    validPrdEndDt = :validPrdEndDt,
                    pinStatusCd = :pinStatusCd,
                    pinStatusNm = :pinStatusNm,
                    upd_date      = :upd_date,
                    detail_yn     = 'Y'
                    where
                    tr_id = :tr_id
                """
                update_data = {
                    "tr_id":tr_id,
                    "brandNm":coupon_info.get("brandNm"),
                    "cnsmPriceAmt":coupon_info.get("cnsmPriceAmt"),
                    "correcDtm":coupon_info.get("correcDtm"),
                    "goodsCd":coupon_info.get("goodsCd"),
                    "goodsNm":coupon_info.get("goodsNm"),
                    "mmsBrandThumImg":coupon_info.get("mmsBrandThumImg"),
                    "recverTelNo":coupon_info.get("recverTelNo"),
                    "sellPriceAmt":coupon_info.get("sellPriceAmt"),
                    "sendBasicCd":coupon_info.get("sendBasicCd"),
                    "sendRstCd":coupon_info.get("sendRstCd"),
                    "sendRstMsg":coupon_info.get("sendRstMsg"),
                    "sendStatusCd":coupon_info.get("sendStatusCd"),
                    "senderTelNo":coupon_info.get("senderTelNo"),
                    "validPrdEndDt":coupon_info.get("validPrdEndDt"),            
                    "pinStatusCd":coupon_info.get("pinStatusCd"),            
                    "pinStatusNm":coupon_info.get("pinStatusNm"),            
                    "upd_date":datetime.now()
                }
                # upd_stmt = update(GiftishowSend).where(GiftishowSend.tr_id == tr_id).values(
                #     # code="0000",
                #     # message="성공",
                #     brandNm=coupon_info.get("brandNm"),
                #     cnsmPriceAmt=coupon_info.get("cnsmPriceAmt"),
                #     correcDtm=coupon_info.get("correcDtm"),
                #     goodsCd=coupon_info.get("goodsCd"),
                #     goodsNm=coupon_info.get("goodsNm"),
                #     mmsBrandThumImg=coupon_info.get("mmsBrandThumImg"),
                #     recverTelNo=coupon_info.get("recverTelNo"),
                #     sellPriceAmt=coupon_info.get("sellPriceAmt"),
                #     sendBasicCd=coupon_info.get("sendBasicCd"),
                #     sendRstCd=coupon_info.get("sendRstCd"),
                #     sendRstMsg=coupon_info.get("sendRstMsg"),
                #     sendStatusCd=coupon_info.get("sendStatusCd"),
                #     senderTelNo=coupon_info.get("senderTelNo"),
                #     validPrdEndDt=coupon_info.get("validPrdEndDt"),            
                #     upd_date=datetime.now()
                # )
                # print(upd_stmt)
                await db.update(update_qry, update_data)
                
            success_count = success_count + 1
        except Exception as e:
            logger.exception(f"Send Goods Info insert/update 실패: {e}")
            fail.extend(row["tr_id"])

        success_count = success_count + 1
    logger.info(f"fetch goods. success:{success_count}, fail:{len(fail)}")

    JOB_ING_SEND = False
    await db.engine.dispose()

# 함수에 파라미터가 없으면 args를 안넣으면 됩니다.
# kargs={"a": 1,"b": 2,"c": 3} 도 가능합니다.
scheduler.add_job(lambda: run(jobBrands()), "interval", seconds=JOB_BRANDS_SEC)
scheduler.add_job(lambda: run(jobGoods()), "interval", seconds=JOB_GOODS_SEC)
scheduler.add_job(lambda: run(jobSends()), "interval", seconds=JOB_SENDS_SEC)

@asynccontextmanager
# @repeat_every(seconds=1)  # 1 hour
async def lifespan(app: FastAPI):
    print('start')
    scheduler.start()
    yield
    print('end')

app = FastAPI(title="Giftishow API", lifespan=lifespan)


# --- 기존 엔드포인트 ---
@app.get("/brands", dependencies=[Depends(verify_ext_access)], summary="브랜드 리스트"
, response_description=
'''
    {
        "result":true,false, 
        "msg":msg, 
        "list":[
        {
            "Brand": {
                "brandIconImg": "https://bizimg.giftishow.com/Resource/brand/20190423_171158178.jpg",
                "brandCode": "BR00002",
                "brandName": "GS25",
                "content": "",
                "category1Seq": "4",
                "category2Seq": "29",
                "crt_date": "2025-09-10T16:38:40",
                "brandBannerImg": "https://bizimg.giftishow.com/Resource/brand/BR_20140729_172540_1.jpg",
                "brandSeq": "691",
                "mmsThumImg": "https://bizimg.giftishow.com/Resource/brand/20190423_171201873.jpg",
                "category1Name": "편의점",
                "category2Name": "인기 TOP100",
                "sort": "3",
                "upd_date": "2025-09-10T17:06:17"
            }
        },...
    }
'''
)
async def get_brands(page: int = Query(1, ge=1), size: int = Query(20, ge=1), db: AsyncSession = Depends(get_async_session)):
    result = True
    msg = ""
    
    offset = (page - 1) * size

    stmt = select(Brand)
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    

    paged_results = await db.execute(
        stmt.order_by(Brand.brandSeq.desc())
        .offset(offset)
        .limit(size)
    )
    # list = [r._mapping for r in paged_results.all()]

    list = []
    
    for r in paged_results.all():
        item = r.Brand.__dict__.copy()
        item.pop("_sa_instance_state", None)
        list.append(item)

    return {"result":result, "page_info":page_info, "msg":msg, "list":list}

@app.get("/goods", dependencies=[Depends(verify_ext_access)], summary="상품 리스트"
, response_description=
'''
    {
        "result": true,
        "msg": "",
        "list": [
            {
                "Goods": {
                    "brandName": "뚜레쥬르",
                    "brandIconImg": "https://bizimg.giftishow.com/Resource/brand/20241218_135627359.jpg",
                    "validPrdDay": "20251010",
                    "exhAgeCd": null,
                    "sellDisRate": null,                
                    "content": "▶상품설명
                        뚜레쥬르의 빵은 맛있고 건강합니다.
                        뚜레쥬르의 빵은 어머니가 만들어주신 것처럼 까다롭게 다져서 고른 재료를 이용하여 매일매일 매장에서 직접 구워냅니다.
                        꼭꼭 씹으면 씹을수록 매장에서 느껴지는 고소함은 바로 원재료 본연의 건강함입니다.
                        빵 본연의 풍미를 느낄 수 있는 뚜레쥬르의 빵을 즐겨보세요.                        
                        ▶이용안내
                        이용시간 : 07:00~23:00 (매장에 따라 운영시간은 변동이 있을 수 있음)
                        
                        ▶유의사항
                        포인트 적립 및 제휴할인 불가합니다.
                        현금으로 교환 불가합니다.
                        잔액 환불 불가합니다.
                        타 쿠폰 및 할인카드와의 중복 사용은 불가합니다.
                        기프티쇼 사용금액 제외 후 추가 결제분에 한해 제휴할인 및 포인트적립 가능합니다.
                        
                        ▶사용불가매장
                        - 마트/휴게소/인천공항 內 입점된 매장은 사용 불가합니다.
                        - 용산역사점",
                    "mmsGoodsImg": "https://bizimg.giftishow.com/Resource/goods/2022/G00000182305/G00000182305_250.jpg",
                    "endDate": "2999-12-31T00:00:00",
                    "mmsReserveFlag": "Y",
                    "rmIdBuyCntFlagCd": "MONTH",
                    "is_sale": "N",
                    "contentAddDesc": null,
                    "discountPrice": "7520",
                    "goodsComId": "S000001864",
                    "goodsStateCd": "SALE",
                    "point_multi": "4.4",
                    "is_naverpay": "N",
                    "goodsNo": "35639",
                    "discountRate": "6.0",
                    "realPrice": "8000",
                    "goodsComName": "뚜레쥬르",
                    "mmsBarcdCreateYn": "Y",
                    "real_point": null,
                    "crt_date": "2025-09-10T16:40:49",
                    "goodsCode": "G00000182305",
                    "goodstypeNm": "일반상품(물품교환형)",
                    "salePrice": "8000",
                    "affiliateId": "뚜레쥬르",
                    "rmCntFlag": "N",                
                    "upd_date": "2025-09-10T16:40:50",
                    "goodsName": "뚜레쥬르 교환권 8천원",
                    "goodsImgS": "https://bizimg.giftishow.com/Resource/goods/2022/G00000182305/G00000182305_250.jpg",
                    "srchKeyword": "뚜레쥬르 교환권 8000원권,빵,베이커리,브레드,bread,뚜레쥬르,뚜레주르,뚜래쥬르,뚜래주르,touslesjours,선물,이벤트,교환권,뚜레쥬르교환권,8천원,팔천원",
                    "saleDateFlagCd": "DAY_SALE",
                    "goodsTypeDtlNm": "베이커리/도넛",                
                    "brandCode": "BR00030",
                    "goodsImgB": "https://bizimg.giftishow.com/Resource/goods/2022/G00000182305/G00000182305.jpg",
                    "validPrdTypeCd": "01",
                    "affilate": "뚜레쥬르",
                    "category1Seq": "2",                
                    "goodsDescImgWeb": null,
                    "limitday": "30",
                    "exhGenderCd": null,
                    "saleDateFlag": "N"
                }
            },,...
        ]
    }
'''
)
async def get_goods(page: int = Query(1, ge=1), size: int = Query(20, ge=1), db: AsyncSession = Depends(get_async_session)):

    result = True
    msg = ""

    offset = (page - 1) * size

    stmt = select(Goods)
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    

    paged_results = await db.execute(
        stmt.order_by(Goods.goodsCode.desc())
        .offset(offset)
        .limit(size)
    )
    # list = [r._mapping for r in paged_results.all()]

    list = []
    
    for r in paged_results.all():
        item = r.Goods.__dict__.copy()
        item.pop("_sa_instance_state", None)
        list.append(item)

    # list = [dict(r.Brand.__dict__) for r in paged_results.all()]

    return {"result":result, "msg":msg, "page_info":page_info, "list":list}
    

@app.post("/send", dependencies=[Depends(verify_ext_access)], summary="쿠폰 전송 요청"
, response_description='''
    {
        "result": true,
        "msg": "",
        "tr_id":"reward_20250911_123456"
    }
''')
async def send_coupon(req: SendRequest, db: AsyncSession = Depends(get_async_session)):
    tr_id = await generate_tr_id(db)

    result = True
    msg = ""
    
    # 1. DB insert (gubun='I')
    stmt = insert(GiftishowSend).values(
        goods_code=req.goods_code,
        mms_msg=req.mms_msg,
        mms_title=req.mms_title,
        callback_no=SEND_NUMBER,
        phone_no=req.phone_no,
        tr_id=tr_id,
        rev_info_yn=req.rev_info_yn,
        rev_info_date=req.rev_info_date,
        rev_info_time=req.rev_info_time,
        template_id=req.template_id,
        banner_id=req.banner_id,
        user_id=USER_ID,
        gubun=req.gubun,
        crt_date=datetime.now()
    ).returning(GiftishowSend.order_no)
    result = await db.execute(stmt)
    order_no = result.scalar()
    await db.commit()
    
    req_dic = req.model_dump()
    req_dic["tr_id"] = tr_id

    # 2. 기프티쇼 발송 API 호출
    send_data = await fetch_coupon_send(req_dic)
    coupon_data = None
    cancel_data = None
    result = True
    msg = ""
    # 3. 결과 처리
    if send_data.get("code") == "0000" and send_data["result"]["code"] == "0000":
        # 쿠폰 확인 API 호출        
        coupon_data = await fetch_coupon_info(tr_id)
    else:
        # 발송 실패 - 취소 처리 요청 후 쿠폰 다시 확인
        cancel_data = await fetch_coupon_cancel(tr_id)
        coupon_data = await fetch_coupon_info(tr_id)
        result = False
        msg = "쿠폰 발송이 실패하였습니다"
    # 결과값 저장
    if result:
        send_result = send_data.get("result").get("result")
        upd_stmt = update(GiftishowSend).where(GiftishowSend.order_no == order_no).values(
            code=send_data.get("code"),
            message=send_data.get("message"),
            pinNo = send_result.get("pinNo") if send_result.get("pinNo") is not None else None,
            orderNo = send_result.get("orderNo") if send_result.get("orderNo") is not None else None,
            couponImgUrl = send_result.get("couponImgUrl") if send_result.get("couponImgUrl") is not None else None,
            upd_date=datetime.now()
        )
        await db.execute(upd_stmt)
        await db.commit()    
    else:
        upd_stmt = update(GiftishowSend).where(GiftishowSend.order_no == order_no).values(
            code=send_data.get("code"),
            message=send_data.get("message"),
            cancel_code=cancel_data.get("code"),
            cancel_message=cancel_data.get("message"),
            detail_yn="Y",
            upd_date=datetime.now()
        )
        await db.execute(upd_stmt)
        await db.commit()    

    if coupon_data is not None and coupon_data.get("code") == "0000":
        coupon_info = coupon_data["result"][0]["couponInfoList"][0]
        upd_stmt = update(GiftishowSend).where(GiftishowSend.order_no == order_no).values(
            # code="0000",
            # message="성공",
            brandNm=coupon_info.get("brandNm"),
            cnsmPriceAmt=coupon_info.get("cnsmPriceAmt"),
            correcDtm=coupon_info.get("correcDtm"),
            goodsCd=coupon_info.get("goodsCd"),
            goodsNm=coupon_info.get("goodsNm"),
            mmsBrandThumImg=coupon_info.get("mmsBrandThumImg"),
            recverTelNo=coupon_info.get("recverTelNo"),
            sellPriceAmt=coupon_info.get("sellPriceAmt"),
            sendBasicCd=coupon_info.get("sendBasicCd"),
            sendRstCd=coupon_info.get("sendRstCd"),
            sendRstMsg=coupon_info.get("sendRstMsg"),
            sendStatusCd=coupon_info.get("sendStatusCd"),
            senderTelNo=coupon_info.get("senderTelNo"),
            validPrdEndDt=coupon_info.get("validPrdEndDt"),    
            pinStatusCd=coupon_info.get("pinStatusCd"),            
            pinStatusNm=coupon_info.get("pinStatusNm"),                    
            detail_yn="Y",
            upd_date=datetime.now()
        )
        await db.execute(upd_stmt)
        await db.commit()
    if result is not True:
        tr_id = ""
    return {"result":result,"msg":msg, "tr_id":tr_id}

@app.post("/info", dependencies=[Depends(verify_ext_access)], summary="쿠폰 정보 요청"
, response_description='''
    {
        "result": true,
        "msg": "",
        "coupon": {
            "rev_info_yn": "N",
            "message": null,
            "cnsmPriceAmt": "1000",
            "sendBasicCd": "2025090800038316816701",
            "upd_date": "2025-09-11T10:25:54",
            "goods_code": "G00000185112",
            "rev_info_date": "",
            "cancel_code": null,
            "correcDtm": "20250910",
            "sendRstCd": "1000",
            "order_no": 29,
            "rev_info_time": "",
            "cancel_message": null,
            "sendRstMsg": "Success",
            "sendStatusCd": "발송완료",
            "mms_msg": "상품이 도착하였습니다",
            "template_id": "",
            "pinNo": null,
            "goodsCd": "G00000185112",
            "senderTelNo": "15886474",
            "mms_title": "상품이 도착하였습니다",
            "banner_id": "",
            "orderNo": "20250908620022",
            "goodsNm": "파리바게뜨 교환권 1,000원",
            "validPrdEndDt": "20251007235959",
            "callback_no": "15886474",
            "user_id": "rewardapp@flutterlap.com",
            "couponImgUrl": null,
            "mmsBrandThumImg": "20171129_151145086.jpg",
            "pinStatusCd": "07",
            "phone_no": "01046183395",
            "gubun": "N",
            "detail_yn": "Y",
            "recverTelNo": "01046183395",
            "pinStatusNm": "구매취소(폐기)",
            "tr_id": "reward_20250908_422615",
            "code": "0000",
            "brandNm": "파리바게뜨",
            "sellPriceAmt": "1000",
            "crt_date": "2025-09-08T10:26:23"
        }
    }
''')
async def info_coupon(tr_id: str =Query(title="tr_id",description="쿠폰 발급시 전송된 tr_id"), db: AsyncSession = Depends(get_async_session)):
    result = False
    msg = ""

    r = await db.execute(select(GiftishowSend).where(GiftishowSend.tr_id==tr_id))
    coupon = r.scalars().first()
    if coupon:
        result = True
    return {"result":result,"msg":msg, "coupon":coupon}
# 쿠폰 취소
@app.post("/cancel", dependencies=[Depends(verify_ext_access)], summary="쿠폰 취소 요청"
, response_description='''
    {
        "result": true,
        "msg": ""
    }
''')
async def cancel_coupon(tr_id: str =Query(title="tr_id",description="쿠폰 발급시 전송된 tr_id"), db: AsyncSession = Depends(get_async_session)):
    
    cancel_data = await fetch_coupon_cancel(tr_id)
    coupon_data = await fetch_coupon_info(tr_id)

    result = False
    msg = ""

    if cancel_data is not None and cancel_data.get("code") == "0000":
        result = True
        msg = "정상처리 되었습니다"

        upd_stmt = update(GiftishowSend).where(GiftishowSend.tr_id == tr_id).values(
            cancel_code=cancel_data.get("code"),
            cancel_message=cancel_data.get("message"),
            detail_yn="Y",
            upd_date=datetime.now()
        )
        await db.execute(upd_stmt)
        await db.commit()    

    if coupon_data is not None and coupon_data.get("code") == "0000":
        coupon_info = coupon_data["result"][0]["couponInfoList"][0]
        upd_stmt = update(GiftishowSend).where(GiftishowSend.tr_id == tr_id).values(
            # code="0000",
            # message="성공",
            # orderNo=coupon_info.get("sendBasicCd"),
            pinStatusCd=coupon_info.get("pinStatusCd"),
            pinStatusNm=coupon_info.get("pinStatusNm"),
            detail_yn="Y",
            upd_date=datetime.now()
        )
        await db.execute(upd_stmt)
        await db.commit()
    
    return {"result":result,"msg":msg}

# --- Swagger에 global header 추가 ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Giftishow API",
        version="1.0.0",
        description="Giftishow API with X-EXT-CODE header auth",
        routes=app.routes,
    )
    # 모든 엔드포인트에 X-EXT-CODE 헤더 추가
    for path in openapi_schema["paths"].values():
        for method in path.values():
            parameters = method.get("parameters", [])
            parameters.append({
                "name": "X-EXT-CODE",
                "in": "header",
                "required": True,
                "schema": {"title": "X-EXT-CODE", "type": "string"},
                "description": "External API code for auth",
            })
            method["parameters"] = parameters
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

def end_log_info(res_body: bytes):
    logger.info(f"RESPONSE: {res_body.decode(errors='ignore')}")

def entry_log_info(endpoint: str):
    logger.info(f"ENDPOINT: {endpoint}")

async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {"type": "http.request", "body": body}
    request._receive = receive

# 로그 기록
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    req_body = await request.body()
    await set_body(request, req_body)
    endpoint = f"{request.method} {request.url.path} {request.url.query} {req_body} {request.client.host} {request.headers}"

    entry_log_info(endpoint)

    response = await call_next(request)

    res_body = b""
    async for chunk in response.body_iterator:
        res_body += chunk

    # task = BackgroundTask(end_log_info, res_body)

    return Response(
        content=res_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        # background=task,
    )