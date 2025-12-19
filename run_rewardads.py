# main.py
import asyncio
from sqlalchemy import select

from pincash_ads.database.async_db import reward_db
from pincash_ads.models.ads_model import Ads
from sqlalchemy.exc import SQLAlchemyError, OperationalError, InterfaceError
import traceback

from pincash_ads.utils.log_util import ads_logger
import httpx

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

        
async def get_ads():
    # 안드로이드, IOS 별로 한번씩 불러오기
    list = []
    await _get_ads(1, 'A', list)
    await _get_ads(1, 'I', list)
    
    for ads in list:
        campaign_id = ads.get("campaign_id", 0)
        campaign_name = ads.get("campaign_name", "")
        campaign_title = ads.get("campaign_title", "")
        campaign_feed_img = ads.get("campaign_feed_img", "")
        campaign_reward_price = ads.get("campaign_reward_price", 0)
        campaign_os_type = ads.get("campaigcampaign_os_typen_id", "")
        campaign_type = ads.get("campaign_type", 0)

        if(campaign_type==8):
            print(campaign_id)


async def main():
    await reward_db._ensure_initialized()
    async with reward_db.async_session() as session:
        # yield session
        try:
            await get_ads()            
        # except HTTPException:
        #     # HTTPException은 FastAPI가 처리하도록 그대로 전파
        #     raise    
        except (SQLAlchemyError, OperationalError, InterfaceError) as e:
            ads_logger.error(f"DB Error: {e}")    
            err_msg = traceback.format_exc()
            ads_logger.error(err_msg)    
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(main())
