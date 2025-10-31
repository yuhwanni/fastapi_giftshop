from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from typing import Optional
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, between, and_, text
from sqlalchemy.orm import selectinload

from reward_app.models.member_model import Member
from reward_app.models.point_history_model import PointHistory
from reward_app.models.quiz_model import Quiz, QuizJoin
from reward_app.utils.common import make_page_info
from reward_app.core.config import make_resp
from datetime import datetime

from reward_app.core.security import get_current_user

import json

from reward_app.service.point_service import save_point

router = APIRouter()

@router.post("/list", name="오늘 진행 중인 퀴즈")
async def list(
    page: int = Form(default=1, ge=1)
    , size: int = Form(default=20, ge=1)
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    
    user_seq = current_user.get('user_seq')
    offset = (page - 1) * size   

    today = datetime.now().strftime('%Y-%m-%d')

    from_qry = """
        FROM
            PC_QUIZ q
            LEFT JOIN PC_QUIZ_JOIN qj ON qj.quiz_seq = q.quiz_seq AND qj.user_seq=:user_seq
        WHERE
            q.del_yn = 'N'
            AND q.start_date <= DATE(:today)
            AND DATE(:today) <= q.end_date
    """

    cnt_qry = f"""
        SELECT count(*) cnt
        {from_qry}
    """
    qry = f"""
        SELECT q.quiz_seq, q.quiz, q.answer, q.hint, q.reward_point, IFNULL(qj.submit_answer, '') submit_answer, IFNULL(qj.is_correct, '') is_correct
        {from_qry}
    """
    
    total_results = await db.execute(text(cnt_qry), {'user_seq':user_seq, 'today': today})
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    
    qry = qry + f" ORDER BY q.quiz_seq DESC LIMIT {offset}, {size}"
    paged_results = await db.execute(text(qry), {'user_seq':user_seq, 'today': today})

    list = [dict(row) for row in paged_results.mappings()]

    return make_resp("S",{"page_info": page_info, "list":list, })


@router.post("/last_list", name="지난 퀴즈")
async def last_list(
    page: int = Form(default=1, ge=1)
    , size: int = Form(default=20, ge=1)
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    
    user_seq = current_user.get('user_seq')
    offset = (page - 1) * size   

    today = datetime.now().strftime('%Y-%m-%d')

    from_qry = """
        FROM
            PC_QUIZ q
            LEFT JOIN PC_QUIZ_JOIN qj ON qj.quiz_seq = q.quiz_seq AND qj.user_seq=:user_seq
        WHERE
            q.del_yn = 'N'            
            AND q.end_date < DATE(:today)
    """

    cnt_qry = f"""
        SELECT count(*) cnt
        {from_qry}
    """
    qry = f"""
        SELECT q.quiz_seq, q.quiz, q.answer, q.hint, q.reward_point, IFNULL(qj.submit_answer, '') submit_answer, IFNULL(qj.is_correct, '') is_correct
        {from_qry}
    """
    
    total_results = await db.execute(text(cnt_qry), {'user_seq':user_seq, 'today': today})
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    
    qry = qry + f" ORDER BY q.quiz_seq DESC LIMIT {offset}, {size}"
    paged_results = await db.execute(text(qry), {'user_seq':user_seq, 'today': today})

    list = [dict(row) for row in paged_results.mappings()]

    return make_resp("S",{"page_info": page_info, "list":list, })


@router.post("/quiz_answer", name="퀴즈 정답 제출")
async def quiz_answer(
    quiz_seq: str =Form(title="퀴즈 번호",description="퀴즈 번호")
    , answer: str =Form(title="정답",description="정답")
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    user_seq = current_user.get('user_seq')

    today = datetime.now().date()
    # 퀴즈가 존재하고 유효기간안에 있는지 확인인
    stmt = select(Quiz).where(and_(
        Quiz.quiz_seq == quiz_seq,
        Quiz.start_date <= today,
        today <= Quiz.end_date,
        Quiz.del_yn == 'N'
    ))
    
    
    r = await db.execute(stmt)
    quiz = r.scalars().first()
    

    if quiz is None:
        return make_resp("E1000")

    # 기존 제출한 내역이 있는지 확인
    stmt = select(QuizJoin).where(and_(
        QuizJoin.quiz_seq == quiz_seq,
        QuizJoin.user_seq == user_seq,
    ))

    r = await db.execute(stmt)
    quiz_join = r.scalars().first() 
    
    if quiz_join is not None:
        return make_resp("E40")
        
    is_correct = "N"
    if answer == quiz.answer:
        is_correct = "Y"
    stmt = insert(QuizJoin).values(
        quiz_seq=quiz_seq,
        user_seq=user_seq,
        submit_answer=answer,
        is_correct=is_correct
    )
    result1 = await db.execute(stmt)
    
    result2 = True

    if is_correct == "Y":
        result2 = await save_point(db, user_seq, "퀴즈정답 포인트 적립", quiz.reward_point, "PC_QUIZ_JOIN", {"quiz_seq": quiz_seq, "user_seq": user_seq}, "Q")
        # ref_info = {"table":"PC_QUIZ_JOIN", "seq": {"quiz_seq": quiz_seq, "user_seq": user_seq}}

        # ref_info_json_string = json.dumps(ref_info, ensure_ascii=False, indent=4)

        # stmt = insert(PointHistory).values(
        #     user_seq = user_seq,
        #     point_name = "포인트적립",
        #     point = quiz.reward_point,
        #     earn_use_type = "E",
        #     point_type = "Q",
        #     ref_info = ref_info_json_string,
        # )
        # result2 = await db.execute(stmt)
        
        # stmt = update(Member).where(Member.user_seq==user_seq).values(
        #     user_point = Member.user_point+quiz.reward_point,
        # )
        # result3 = await db.execute(stmt)

    await db.commit()     
    if result1 and result2:
        return make_resp("S", {"is_correct":is_correct})
    else:
        return make_resp("E41")