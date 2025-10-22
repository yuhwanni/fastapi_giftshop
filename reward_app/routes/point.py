from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, text
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy import func

from enum import Enum
from reward_app.core.security import get_current_user

from reward_app.models.notice_model import Notice
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
router = APIRouter()


class EarnUseType(str, Enum):
    EARN = "E"  # 적립
    USE = "U"   # 사용


@router.get("/list", name="포인트 리스트")
async def list(
    from_date: str =Query(title="from_date",description="검색 시작일 Y-m-d")
    , to_date: str =Query(title="to_date",description="검색 종료일 Y-m-d")
    , use_type: EarnUseType = Query(title="point_type",description="E 적립, U 사용", )
    , page: int = Query(1, ge=1), size: int = Query(20, ge=1)
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user)
    ):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    user_seq = current_user.get('user_seq')
    offset = (page - 1) * size   


    from_qry = """
        FROM
            PC_POINT_HISTORY PH            
        WHERE
            PH.del_yn = 'N' AND PH.user_seq=:user_seq
    """

    cnt_qry = f"""
        SELECT count(*) cnt
        {from_qry}
    """
    qry = f"""
        SELECT PH.point_name, PH.point, DATE_FORMAT(PH.crt_date, '%Y-%m-%d') crt_date
        {from_qry}
    """
    
    total_results = await db.execute(text(cnt_qry), {'user_seq':user_seq})
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    
    qry = qry + f" ORDER BY PH.crt_date DESC LIMIT {offset}, {size}"
    paged_results = await db.execute(text(qry), {'user_seq':user_seq})

    list = [dict(row) for row in paged_results.mappings()]

    return make_resp("S",{"page_info": page_info, "list":list, })

@router.get("/info", name="현재 포인트, 30일 내 소멸 예정 포인트, 총 적립 포인트")
async def info(    
    db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user)
    ):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    user_seq = current_user.get('user_seq')
    qry = f"""
        SELECT
            (
                ( SELECT IFNULL(SUM(PH.point),0) FROM PC_POINT_HISTORY PH WHERE PH.del_yn = 'N' AND PH.user_seq=:user_seq AND PH.earn_use_type='E' )
                -
                ( SELECT IFNULL(SUM(PH.point),0) FROM PC_POINT_HISTORY PH WHERE PH.del_yn = 'N' AND PH.user_seq=:user_seq AND PH.earn_use_type='U' )
            ) current_point,            
            ( SELECT IFNULL(SUM(PH.point),0) FROM PC_POINT_HISTORY PH WHERE PH.del_yn = 'N' AND PH.user_seq=:user_seq AND DATE_ADD(PH.crt_date, INTERVAL 1 YEAR) < DATE_ADD(NOW(), INTERVAL 30 DAY)) expiring_point,
            ( SELECT IFNULL(SUM(PH.point),0) FROM PC_POINT_HISTORY PH WHERE PH.del_yn = 'N' AND PH.user_seq=:user_seq ) total_point
    """

    result = await db.execute(text(qry), {'user_seq':user_seq})
    
    point = result.mappings().first()
    
    return make_resp("S",point)

