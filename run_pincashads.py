# main.py
import asyncio
from sqlalchemy import select, update, not_
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert

from pincash_ads.database.async_db import reward_db
from pincash_ads.models.ads_model import Ads
from sqlalchemy.exc import SQLAlchemyError, OperationalError, InterfaceError
import traceback

from pincash_ads.utils.log_util import ads_logger
import httpx

def map_api_to_ads(item: dict) -> Ads:
    return Ads(
        ads_id=item.get("campaign_id", 0),
        ads_name=item.get("campaign_name", ""),
        ads_title=item.get("campaign_title",""),
        ads_condition=item.get("campaign_condition",""),        
        ads_feed_img=item.get("campaign_feed_img",""),
        ads_reward_price=item.get("campaign_reward_price",0),
        ads_os_type=item.get("campaign_os_type", "ALL"),
        ads_type=item.get("campaign_type", "")
    )

async def _get_ads(page:int, os_type:str, list: list | None = None):
    url = 'https://pcapi.pincash.co.kr/pin/offer.cash'

    params = {
        "aff_key": "1dlPvLmOMR",
        "page": page,
        "limit": 3000,
        "ads_os_type": os_type
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, data=params)
        data = resp.json()

        items = data.get("data", {}).get("items", [])

        list.extend(items)
        
        pageinfo = data.get("data", {}).get("pageinfo", {})
        total_pages = pageinfo.get("total_pages", 1)
        if total_pages>page:
            page = page+1
            await _get_ads(page, os_type)

        
async def get_ads(session: Session):
    # 안드로이드, IOS 별로 한번씩 불러오기
    list = []
    await _get_ads(1, 'A', list)
    await _get_ads(1, 'I', list)

    ads_objects = [map_api_to_ads(item) for item in list]
    live_ads=[]
    for ads in ads_objects:       
        
        stmt = insert(Ads).values(
            ads_id=ads.ads_id,
            ads_name=ads.ads_name,
            ads_title=ads.ads_title,
            ads_condition=ads.ads_condition,
            ads_feed_img=ads.ads_feed_img,
            ads_reward_price=ads.ads_reward_price,
            ads_os_type=ads.ads_os_type,        
            ads_type=ads.ads_type,
            live_yn="Y"
        ).on_duplicate_key_update(
            ads_name=ads.ads_name,
            ads_title=ads.ads_title,
            ads_condition=ads.ads_condition,
            ads_feed_img=ads.ads_feed_img,
            ads_reward_price=ads.ads_reward_price,
            ads_os_type=ads.ads_os_type,
            ads_type=ads.ads_type,
            live_yn="Y"      
        )
        await session.execute(stmt)
        
        live_ads.append(ads.ads_id)
    # 핀캐시 미노출 변경
    
    if len(live_ads)>0:
        stmt = (
            update(Ads)
            .where(Ads.ads_id.notin_(live_ads))
            .values(live_yn="N")
        )

        await session.execute(stmt)

    await session.commit()

async def main():
    await reward_db._ensure_initialized()
    async with reward_db.async_session() as session:
        # yield session
        try:
            await get_ads(session)            
        # except HTTPException:
        #     # HTTPException은 FastAPI가 처리하도록 그대로 전파
        #     raise    
        except (SQLAlchemyError, OperationalError, InterfaceError) as e:
            ads_logger.error(f"DB Error: {e}")    
            err_msg = traceback.format_exc()
            ads_logger.error(err_msg)    
        finally:
            await session.close()
            await reward_db.close()


if __name__ == "__main__":
    asyncio.run(main())
