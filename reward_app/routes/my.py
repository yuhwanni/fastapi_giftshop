from fastapi import APIRouter, Depends, HTTPException, status, Query
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

@router.get("/info", name="내정보")
async def list(
    db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    
    user_seq = current_user.get('user_seq')

    r = await db.execute(select(
        # Member.user_seq,             # 회원 고유번호 (PK, AUTO_INCREMENT)
        Member.user_email,           # 사용자 이메일 (로그인 ID, 고유값)
        # Member.user_sns_key,         # SNS 고유 키 (SNS 로그인 시 사용)
        # Member.user_pwd,             # 사용자 비밀번호 (암호화 저장)
        # Member.user_pwd2,            # 임시 비밀번호 (비밀번호 변경용)
        Member.user_name,            # 사용자 이름
        Member.nickname,             # 닉네임 (표시용 이름)
        Member.user_phone,           # 전화번호
        Member.user_gender,          # 성별 (F:여성, M:남성, U:미확인)
        Member.user_birth,           # 생년월일 (YYYY-MM-DD)
        Member.solar_lunar,          # 생일 구분 (S:양력, L:음력, N:선택안함)
        Member.time_of_birth,        # 태어난 시각 (HH:MM)
        Member.user_location,        # 지역 정보 (선택 입력)
        # Member.user_token,           # 푸시 토큰 (알림용)
        Member.device_id,            # 디바이스 ID (기기 식별)
        Member.user_point,           # 보유 포인트
        Member.referral_code,        # 추천인 코드
        Member.user_stat,            # 회원 상태 (Y:활성, N:중지)
        Member.user_sns_type,        # 가입 유형 (NS:일반, G:구글, N:네이버, K:카카오)
        Member.user_img,             # 프로필 이미지 URL
        Member.last_login_date,      # 마지막 로그인 일자
        Member.push_status,          # 푸시 알림 동의 여부 (Y/N)
        Member.push_date,            # 푸시 설정 등록/수정일
        # Member.terms_yn,             # 이용약관 동의 여부
        # Member.privacy_yn,           # 개인정보 수집 이용 동의 여부
        Member.marketing_yn,         # 마케팅 수신 동의 여부
        # Member.crt_date,             # 생성일자
        # Member.crt_id,               # 생성자 ID
        # Member.upd_date,             # 수정일자
        # Member.upd_id,               # 수정자 ID
        # Member.del_date              # 탈퇴일자        
    ).where(Member.user_seq==user_seq))
    
    # member = r.scalars().first()
    member = (r.mappings().first())
    return make_resp("S",{"data":member})


@router.get("/info_update/proc", name="계정정보 변경경")
async def last_list(page: int = Query(1, ge=1), size: int = Query(20, ge=1), db: AsyncSession = Depends(get_async_session)
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


@router.get("/quiz_answer", name="퀴즈 정답 제출")
async def quiz_answer(
    quiz_seq: str =Query(title="퀴즈 번호",description="퀴즈 번호")
    , answer: str =Query(title="정답",description="정답")
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
        return make_resp("E100")

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