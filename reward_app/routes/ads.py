from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form
from typing import Optional
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert,update,func, and_

from reward_app.models.ads_complete_model import AdsComplete
from reward_app.models.member_model import Member
from reward_app.core.config import make_resp
from reward_app.utils.params import DuplicateYn
from reward_app.service.point_service import save_point

router = APIRouter()

# http://15.164.103.3/ads/callback?ads_id={campaign_id}&user_seq={ptn_id}&adid={adid_or_idfa}&payout={payout}&user_cost={user_cost}&ads_name={campaign_name}
@router.post("/callback", name="광고적립 콜백(특정 아이피만 가능)")
async def callback(
    request: Request
    , ads_id: str =Query(description="광고 아이디")
    , ads_name: str =Query(description="광고명")    
    , user_seq: str =Query(description="사용자키")
    , adid: str =Query(description="adid or idfa")
    , payout: str =Query(description="매체단가")
    , user_cost: str =Query(description="유저 리워드")    
    , unq_campaign: DuplicateYn =Query(description="중복지급 가능여부")    
    , db: AsyncSession = Depends(get_async_session)    
    ):
    host_ip = request.client.host
    
    if host_ip not in["127.0.0.1","211.43.213.178"]:
        return ""
    
    # 요청이 왔으니 우선 넣는다
    stmt = insert(AdsComplete).values(
        ads_id=ads_id,
        ads_name=ads_name,
        user_seq=user_seq,
        adid=adid,
        payout=payout,
        user_cost=user_cost,
        unq_campaign=unq_campaign,
        host_ip=host_ip,
    ).returning(AdsComplete.complete_seq)
    result = await db.execute(stmt)
    complete_seq = result.scalar()
    if not result:
        return make_resp("E101")

    await db.commit()

    # 중복 지급 가능 일 경우 체크
    if unq_campaign=="N":
        stmt = select(AdsComplete).where(and_(AdsComplete.ads_id == ads_id,AdsComplete.user_seq == user_seq, AdsComplete.point_add_yn=="Y"))
        result = await db.execute(stmt)
        ads_complete = result.scalars().first()
        
        if ads_complete is not None:
            return make_resp("E100")

    # 사용자 있는지 확인
    stmt = select(Member).where(Member.user_seq==user_seq)
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0

    if total_count == 0:
        return make_resp("E900")
    
    result2 = await save_point(db, user_seq, f"{ads_name} 광고적립", user_cost, "PC_ADS_COMPLETE", {"complete_seq": complete_seq}, "A")
    
    stmt = update(AdsComplete).where(AdsComplete.complete_seq==complete_seq).values(
        point_add_yn="Y"
    )
    result3 = await db.execute(stmt)


    if result2 and result3:
        await db.commit()
        return make_resp("S")
    else:
        await db.rollback()
        return make_resp("E102")
