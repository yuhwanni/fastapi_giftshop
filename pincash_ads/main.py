# main.py
import asyncio
from sqlalchemy import select

from pincash_ads.database.async_db import reward_db
from pincash_ads.models.ads_model import Ads
from sqlalchemy.exc import SQLAlchemyError, OperationalError, InterfaceError
import traceback

from pincash_ads.utils.log_util import ads_logger

async def start_job():
    print('hi')

async def main():
    await reward_db._ensure_initialized()
    async with reward_db.async_session() as session:
        # yield session
        try:
            start_job()
            yield session
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
