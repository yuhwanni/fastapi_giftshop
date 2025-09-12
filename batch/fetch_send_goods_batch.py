import os
import sys
# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# fetch_brand_goods_batch.py

import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
import httpx

from utils.giftishow import fetch_coupon_info



from database.db_core import AsyncDatabase, get_async_db, get_async_session
from models.brand_model import Brand
from models.goods_model import Goods
from utils.slack import send_slack  # 슬랙 알림 유틸
from datetime import datetime

from sqlalchemy import update
from sqlalchemy import select
from models.giftishow_send_model import GiftishowSend

load_dotenv()

# async_db = get_async_db()
async_db = get_async_db()

# 로깅 설정
today = datetime.now().strftime("%Y%m%d")
log_dir = os.path.join("logs", today)
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "send_goods_batch.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def process_infos(db):
    start, size = 1, 100
    success_count, fail = 0, []
    qry = """
        select tr_id from API_GIFTISHOW_SEND where detail_yn = 'N'
    """
    
    
    list = await db.fetchall(qry,{})
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

    return success_count, fail


async def main():
    start_time = datetime.now()    
    try:
        logger.info("Start Send Goods Info batch...")
        info_count, info_fail = await process_infos(async_db)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        message = (
            f"✅ Send Goods Info 배치 완료\n"
            f"Send Goods Info 처리: {info_count}건 (실패: {len(info_fail)})\n"
            f"소요 시간: {duration:.2f}초"
        )
        
        await send_slack(message)
        logger.info(message)

    except Exception as e:
        logger.exception(f"배치 실행 중 오류 발생: {e}")
        await send_slack(f"❌ 배치 실행 중 오류 발생: {e}")
    finally:
        print('end')
        await async_db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
