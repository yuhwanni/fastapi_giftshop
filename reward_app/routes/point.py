from fastapi import APIRouter, Depends, Form
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, text
from sqlalchemy import insert
from sqlalchemy import update
from sqlalchemy import func


from reward_app.core.security import get_current_user

from reward_app.models.notice_model import Notice
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp

from reward_app.models.point_history_model import PointHistory

from reward_app.utils.params import EarnUseType

from datetime import date
import calendar

router = APIRouter()


@router.post("/list", name="포인트 리스트")
async def list(
    from_date: str = Form(default="", title="from_date", description="검색 시작일 Y-m-d. 빈값일 경우 현재 월의 1일"),
    to_date: str = Form(default="", title="to_date", description="검색 종료일 Y-m-d. 빈값일 경우 현재 월의 말일일"),
    use_type: EarnUseType = Form(title="point_type", description="E 적립, U 사용"),
    page: int = Form(default=1, ge=1),
    size: int = Form(default=20, ge=1),
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    # 1) from_date/to_date 문자열을 date로 파싱 + 기본값 세팅
    today = date.today()

    if from_date:
        # "YYYY-MM-DD" -> date
        from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
    else:
        from_date_obj = today.replace(day=1)

    if to_date:
        to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
    else:
        last_day = calendar.monthrange(today.year, today.month)[1]
        to_date_obj = today.replace(day=last_day)

    # 2) 날짜 범위를 datetime 범위로 변환 (to_date는 다음날 00:00 미만)
    from_dt = datetime.combine(from_date_obj, time.min)  # 00:00:00
    to_dt_exclusive = datetime.combine(to_date_obj + timedelta(days=1), time.min)  # 다음날 00:00:00

    user_seq = current_user.get("user_seq")
    offset = (page - 1) * size

    conditions = [
        PointHistory.user_seq == user_seq,
        PointHistory.earn_use_type == use_type,
        PointHistory.crt_date >= from_dt,
        PointHistory.crt_date < to_dt_exclusive,
    ]

    # 3) 조회
    stmt = (
        select(
            PointHistory.point_name,
            PointHistory.point,
            func.DATE_FORMAT(PointHistory.crt_date, "%Y-%m-%d").label("crt_date"),
            PointHistory.earn_use_type,
        )
        .where(*conditions)
        .order_by(PointHistory.crt_date.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    rows = result.mappings().all()

    # 4) count
    count_stmt = select(func.count()).select_from(PointHistory).where(*conditions)
    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar_one()

    # 5) sum
    sum_stmt = select(func.coalesce(func.sum(PointHistory.point), 0)).select_from(PointHistory).where(*conditions)
    sum_result = await db.execute(sum_stmt)
    total_point = sum_result.scalar_one()

    page_info = make_page_info(total_count, page, size)

    return make_resp(
        "S",
        {
            "from_date": from_date_obj.strftime("%Y-%m-%d"),
            "to_date": to_date_obj.strftime("%Y-%m-%d"),
            "total_point": total_point,
            "page_info": page_info,
            "list": rows,
        },
    )


@router.post("/info", name="현재 포인트, 30일 내 소멸 예정 포인트, 총 적립 포인트")
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

