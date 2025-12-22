from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form

from typing import List, Optional

from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert,update,func, and_

from sqlalchemy import desc, asc


from reward_app.models.ads_complete_model import AdsComplete
from reward_app.models.member_model import Member
from reward_app.core.config import make_resp
from reward_app.utils.params import DuplicateYn
from reward_app.service.point_service import save_point
from reward_app.models.ads_model import Ads
from reward_app.utils.log_util import api_logger

from reward_app.core.security import get_current_user

from reward_app.utils.common import generate_clickid

from reward_app.models.ads_complete_model import AdsComplete

router = APIRouter()

# http://15.164.103.3/ads/callback?ads_id={campaign_id}&user_seq={ptn_id}&adid={adid_or_idfa}&payout={payout}&user_cost={user_cost}&ads_name={campaign_name}
@router.get("/callback", name="광고적립 콜백(특정 아이피만 가능)")
async def callback(
    request: Request
    , ads_id: str =Query(description="광고 아이디")
    , clickid: str =Query(description="클릭 아이디")
    , ads_name: str =Query(description="광고명")    
    , user_seq: str =Query(description="사용자키")
    , adid: str =Query(description="adid or idfa")
    , payout: str =Query(description="매체단가")
    , user_cost: str =Query(description="유저 리워드")    
    , unq_campaign: DuplicateYn =Query(description="중복지급 가능여부")    
    , db: AsyncSession = Depends(get_async_session)    
    ):
    host_ip = request.client.host
    api_logger.info(f"{host_ip} callback")
    if host_ip not in["127.0.0.1","211.43.213.178"]:
        return ""
    
    # clickid 확인
    stmt = select(AdsComplete).where(and_(AdsComplete.clickid == clickid))
    result = await db.execute(stmt)
    ads_complete = result.scalars().first()

    


    


@router.post("/feed_list", name="피드광고")
async def feed_list(
    request: Request
    , limit: int =Form(default=5, description="광고 갯수")
    , platforms: Optional[List[str]] = Form(None, description="os 타입 기본 ['A', 'W', 'ALL'], PC:전체,WEB, A:Android,WEB,전체, I:iOS,WEB 전체")
    , db: AsyncSession = Depends(get_async_session)    
    ):

    platforms = [x for x in (platforms or []) if x.strip()]

    platforms = platforms or ["A", "W", "ALL"]
    
    stmt = select(Ads).where(and_(Ads.ads_os_type.in_(platforms), Ads.show_yn == "Y",Ads.ads_type == "8", Ads.live_yn == 'Y')).order_by(Ads.ads_order.asc(), Ads.upd_date.desc()).limit(limit)
    result = await db.execute(stmt)
    list = result.scalars().all()
    return make_resp("S", {"list":list})

@router.post("/clickid", name="광고 아이디 가져오기")
async def clickid(
    db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user)
    ):

    clickid = await generate_clickid(db, 10)
    
    if not clickid:
        return make_resp("E700")

    user_seq = current_user.get('user_seq')

    stmt = insert(AdsComplete).values(
        user_seq=user_seq,
        clickid=clickid
    ).returning(AdsComplete.complete_seq)
    result = await db.execute(stmt)
    complete_seq = result.scalar()

    if not complete_seq:
        return make_resp("E701")
    await db.commit()

    return make_resp("S", {"clickid":clickid})
