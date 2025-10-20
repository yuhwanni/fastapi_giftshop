# fetch_brand_goods_batch.py
import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
import httpx

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from giftshop_app.database.db_core import AsyncDatabase, get_async_db, get_async_session
from giftshop_app.models.brand_model import Brand
from giftshop_app.models.goods_model import Goods
from giftshop_app.utils.slack import send_slack  # 슬랙 알림 유틸
from datetime import datetime


load_dotenv()

async_db = get_async_db()

API_BRAND_URL = os.getenv("BIZAPI_URL", "https://bizapi.giftishow.com/bizApi/brands")+"/"+os.getenv("BIZAPI_BRAND", "brands")
API_GOODS_URL = os.getenv("BIZAPI_URL", "https://bizapi.giftishow.com/bizApi/brands")+"/"+os.getenv("BIZAPI_GOODS", "goods")

API_CODE_BRAND = os.getenv("API_CODE_BRAND", "0102")
API_CODE_GOODS = os.getenv("API_CODE_GOODS", "0101")
AUTH_CODE = os.getenv("CUSTOM_AUTH_CODE")
AUTH_TOKEN = os.getenv("CUSTOM_AUTH_TOKEN")
DEV_YN = os.getenv("DEV_YN", "Y")

# 로깅 설정
today = datetime.now().strftime("%Y%m%d")
log_dir = os.path.join("logs", today)
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "batch.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def parse_end_date(date_str: str):
    if not date_str:
        return None
    try:
        # "2999-12-30T15:00:00.000+0000" -> naive datetime
        dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
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


async def process_brands(db):
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
            "sort": str(b.get("sort")) if b.get("sort") else None
        })

    try:
        await db.insert_many("API_GIFTISHOW_BRANDS", db_data, update_on_duplicate=True)
        success = len(db_data)
    except Exception as e:
        logger.exception(f"Brand insert/update 실패: {e}")
        fail = [b["brandCode"] for b in db_data]

    return success, fail


async def process_goods(db):
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

    return success_count, fail


async def main():
    start_time = datetime.now()    
    try:
        logger.info("Start Brand batch...")
        brand_count, brand_fail = await process_brands(async_db)

        logger.info("Start Goods batch...")
        goods_count, goods_fail = await process_goods(async_db)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        message = (
            f"✅ Brand & Goods 배치 완료\n"
            f"Brand 처리: {brand_count}건 (실패: {len(brand_fail)})\n"
            f"Goods 처리: {goods_count}건 (실패: {len(goods_fail)})\n"
            f"소요 시간: {duration:.2f}초"
        )
        if brand_fail:
            message += f"\nBrand 실패 항목: {brand_fail[:20]}{'...' if len(brand_fail) > 20 else ''}"
        if goods_fail:
            message += f"\nGoods 실패 항목: {goods_fail[:20]}{'...' if len(goods_fail) > 20 else ''}"

        await send_slack(message)
        logger.info(message)

    except Exception as e:
        logger.exception(f"배치 실행 중 오류 발생: {e}")
        await send_slack(f"❌ 배치 실행 중 오류 발생: {e}")
    finally:
        await async_db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
