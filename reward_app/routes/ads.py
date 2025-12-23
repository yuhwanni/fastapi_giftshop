from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form
from fastapi.responses import RedirectResponse


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

import httpx
from fastapi import HTTPException


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

    if not ads_complete:
        return make_resp("E105")

    # 기지급 되었을 경우
    if ads_complete.point_add_yn=="Y":
        return make_resp("E106")

    stmt = update(AdsComplete).where(AdsComplete.complete_seq==ads_complete.complete_seq).values(
        ads_id=ads_id,
        ads_name=ads_name,        
        adid=adid,
        payout=payout,
        user_cost=user_cost,
        unq_campaign=unq_campaign,
        host_ip=host_ip,
    )
    result1 = await db.execute(stmt)

    if not result1:
        return make_resp("E107")

    await db.commit()

    # 다시 조회
    stmt = select(AdsComplete).where(and_(AdsComplete.clickid == clickid))
    result = await db.execute(stmt)
    ads_complete = result.scalars().first()

    stmt = select(Member).where(Member.user_seq==user_seq)
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0

    if total_count == 0:
        return make_resp("E900")

    result2 = await save_point(db, user_seq, f"{ads_name} 광고적립", user_cost, "PC_ADS_COMPLETE", {"complete_seq": ads_complete.complete_seq}, "A")
    
    stmt = update(AdsComplete).where(AdsComplete.complete_seq==ads_complete.complete_seq).values(
        point_add_yn="Y"
    )
    result3 = await db.execute(stmt)
  
    if result2 and result3:
        await db.commit()
        return make_resp("S")
    else:
        await db.rollback()
        return make_resp("E102")

@router.post("/join_ads", name="광고참여", description='''
{
  "code": "S",
  "msg": "요청성공",
  "url": "https://join.com/join"
}
''')
async def clickid(
    request: Request
    , campaign_id: str =Form()
    # , aff_key: str =Form()
    , adid: str =Form(default="")
    , idfa: str =Form(default="")
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user)
    ):
    
    join_ip = request.client.host

    if not adid and not idfa:
        return make_resp("E110")
    clickid = await generate_clickid(db, 10)
        
    if not clickid:
        return make_resp("E103")

    user_seq = current_user.get('user_seq')

    # 클릭 아이디 생성후 핀캐시 api 호출
    api_url = 'https://pcapi.pincash.co.kr/pin/join.cash'

    params = {
        "aff_key": "1dlPvLmOMR",
        "campaign_id": campaign_id,
        "ptn_id": user_seq,
        "adid": adid,
        "idfa": idfa,
        "externalid": clickid
    }
    
    code = ""
    join_url = ""
    msg = ""

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            resp = await client.post(api_url, data=params)
            resp.raise_for_status()

            data = resp.json()
            code = data.get("code", "")
            join_url = data.get("url", "")
            msg = data.get("code", "")

        except httpx.TimeoutException:
            return make_resp("E108", {"status_code":504, "detail":"Upstream service timeout"})
        except httpx.HTTPStatusError as e:
            return make_resp("E108", {"status_code":502, "detail":f"Upstream error {e.response.status_code}"})
        except httpx.RequestError as e:
            return make_resp("E108", {"status_code":502, "detail":f"Upstream request failed: {str(e)}"})
        except ValueError:
            return make_resp("E108", {"status_code":502, "detail":"Invalid JSON from upstream"})
    if not code:
        return make_resp("E108", {})

    if code!="200":
        return make_resp("E109", {"api_code":code, "api_msg":msg})
    
    stmt = insert(AdsComplete).values(
        user_seq=user_seq,
        clickid=clickid,
        join_ip=join_ip,
        ads_id=campaign_id
    ).returning(AdsComplete.complete_seq)
    result = await db.execute(stmt)
    complete_seq = result.scalar()

    if not complete_seq:
        return make_resp("E104")
    await db.commit()
    
    # return RedirectResponse(
    #     url=join_url,
    #     status_code=302
    # )

    return make_resp("S", {"url":join_url})

    


@router.post("/feed_list", name="피드광고")
async def feed_list(
    request: Request
    , limit: int =Form(default=5, description="광고 갯수")
    , platforms: Optional[List[str]] = Form(None, description="os 타입 기본 ['A', 'W', 'ALL'], A:안드로이드, I:ios, W:웹, ALL:전체")
    # PC:전체,WEB, A:Android,WEB,전체, I:iOS,WEB 전체
    , db: AsyncSession = Depends(get_async_session)
    ):

    platforms = [x for x in (platforms or []) if x.strip()]

    platforms = platforms or ["A", "W", "ALL"]
    
    stmt = select(Ads).where(and_(Ads.ads_os_type.in_(platforms), Ads.show_yn == "Y",Ads.ads_type == "8", Ads.live_yn == 'Y')).order_by(Ads.ads_order.asc(), Ads.upd_date.desc()).limit(limit)
    result = await db.execute(stmt)
    list = result.scalars().all()
    return make_resp("S", {"list":list})

