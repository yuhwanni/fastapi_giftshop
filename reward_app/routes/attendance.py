from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, between, and_, text
from sqlalchemy.orm import selectinload

from reward_app.models.attendance_model import Attendance
from reward_app.models.member_model import Member
from reward_app.models.point_history_model import PointHistory

from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
from datetime import datetime
import calendar


from reward_app.core.security import get_current_user
from reward_app.service.point_service import save_point


import os
from dotenv import load_dotenv

import json

router = APIRouter()


@router.get("/list", name="출석 리스트")
async def quiz_answer(
    ym: str =Query(default=None, description="년월(Y-m) 기본값 현재 년월")
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    user_seq = current_user.get('user_seq')

    if ym is None:
        ym = datetime.now().strftime("%Y-%m")

    year, month = map(int, ym.split("-"))

    # 마지막 일 구하기
    last_day = calendar.monthrange(year, month)[1]

    # 1일부터 마지막일까지 날짜 문자열 리스트 생성
    days = [f"{ym}-{day:02d}" for day in range(1, last_day + 1)]    

    sql_days = ", ".join([f"'{ym}-{day:02d}'" for day in range(1, last_day + 1)])

    sql_parts = [f"SELECT '{ym}-{day:02d}' AS base_date" for day in range(1, last_day + 1)]
    
    
    qry = f"""
        WITH RECURSIVE T_TEMP_DATES AS (
            SELECT '{ym}-01' AS DT
        UNION
            SELECT DATE_ADD(T_TEMP_DATES.DT, INTERVAL 1 DAY) FROM T_TEMP_DATES WHERE DATE_ADD(T_TEMP_DATES.DT, INTERVAL 1 DAY) <=   '{ym}-{last_day:02d}'
        )
        SELECT 
            TD1.DT ymd,
            A.point,
            CASE 
                WHEN A.user_seq IS NOT NULL AND A.user_seq <> '' THEN 'Y'
                ELSE 'N'
            END AS is_complete
        FROM  T_TEMP_DATES TD1
        LEFT JOIN PC_ATTENDANCE A ON A.attendance_date = TD1.DT AND A.user_seq=:user_seq   
    """

    paged_results = await db.execute(text(qry), {'user_seq':user_seq})

    list = [dict(row) for row in paged_results.mappings()]

    return list

    
    # user_seq = current_user.get('user_seq')

    
@router.get("/check", name="출석 체크하기")
async def quiz_answer(
    ym: str =Query(default=None, description="년월(Y-m) 기본값 현재 년월")
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    user_seq = current_user.get('user_seq')

    

    today = datetime.now().date()
    # 퀴즈가 존재하고 유효기간안에 있는지 확인인
    stmt = select(Attendance).where(and_(
        Attendance.user_seq == user_seq,
        Attendance.attendance_date == today
    ))
    
    
    r = await db.execute(stmt)
    Attendance = r.scalars().first()
    

    if Attendance is not None:
        return make_resp("S", {"msg":"오늘 출석 완료"})

    load_dotenv()
    
    ATTENDANCE_POINT = int(os.getenv("ATTENDANCE_POINT"))

    stmt = insert(Attendance).values(
        user_seq = user_seq,
        attendance_date = today,
        point = ATTENDANCE_POINT
    )
    result1 = await db.execute(stmt)
    
    result2 = True

    if result1 and ATTENDANCE_POINT > 0:
        result2 = await save_point(db, user_seq, "출석 체크 적립", ATTENDANCE_POINT, "PC_ATTENDANCE", {"attendance_date": today, "user_seq": user_seq}, "T")

    await db.commit()     

    if result1 and result2:
        return make_resp("S")
    else:
        return make_resp("E21")