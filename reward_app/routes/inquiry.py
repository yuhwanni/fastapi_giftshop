from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert, update, delete, func, between, and_, text
from sqlalchemy.orm import selectinload

from reward_app.models.member_model import Member

from reward_app.models.inquiry_model import Inquiry, InquiryFile
from reward_app.utils.common import make_page_info, resize_image
from reward_app.core.config import make_resp
from datetime import datetime

from reward_app.core.security import get_current_user

import json

from reward_app.service.point_service import save_point, reduce_point

import secrets

import os
from dotenv import load_dotenv
router = APIRouter()

@router.post("/list", name="문의 리스트")
async def list(page: int = Query(1, ge=1), size: int = Query(20, ge=1), db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):
    # list = await db.execute(select(Notice).where(Notice.user_email==email))
    
    user_seq = current_user.get('user_seq')
    offset = (page - 1) * size   

    stmt = select(Inquiry).where(and_(Inquiry.del_yn=="N", Inquiry.user_seq))
    total_results = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total_count = total_results.scalar() or 0  # 전체 데이터 개수

    page_info = make_page_info(total_count, page, size)    

    paged_results = await db.execute(
        stmt.order_by(Inquiry.crt_date.desc())
        .offset(offset)
        .limit(size)
    )

    list = []
    
    for r in paged_results.all():
        item = r.Inquiry.__dict__.copy()
        item.pop("_sa_instance_state", None)
        list.append(item)

    # list = [r._mapping for r in paged_results.all()]

    return make_resp("S", {"page_info": page_info, "list":list, })


@router.post("/request/proc", name="문의신청")
async def request_proc(
    title: str =Query(title="제목",description="제목")
    , content: str =Query(title="내용",description="내용")
    , images: List[UploadFile] = File(default=[])
    , db: AsyncSession = Depends(get_async_session)
    , current_user = Depends(get_current_user), 
):    
    user_seq = current_user.get('user_seq')

    # 사용자 있는지 확인    
    result = await db.execute(select(Member).where(Member.user_seq==user_seq))
    member = result.scalar_one_or_none()
    if member is None:
        return make_resp("E900")
    
    load_dotenv()
    IMAGE_FILE_SIZE = os.getenv("IMAGE_FILE_SIZE", "10")
    IMAGE_FILE_PATH = os.getenv("IMAGE_FILE_PATH", "inquiry_file")

    IMAGE_FILE_SIZE = int(IMAGE_FILE_SIZE)
    # 첨부된 이미지가 있을 경우 체크
    for image in images:
        if not image.content_type.startswith("image"):
            return make_resp("E400")
        if len(await image.read()) > IMAGE_FILE_SIZE * 1024 * 1024:
            return make_resp("E401", {"msg":f"{IMAGE_FILE_SIZE} 이하 파일만 첨부 가능합니다"})

    stmt = insert(Inquiry).values(
        user_seq=user_seq,
        title=title,
        content=content,
        file_cnt=len(images)
    ).returning(Inquiry.inquiry_seq)
    result = await db.execute(stmt)
    inquiry_seq = result.scalar()

    success_image_seq_arr = []
    # 이미지들 저장
    for image in images:
        # 원본 이미지 파일명
        file_name = image.filename
        random_name = secrets.token_urlsafe(16)
        saved_file_name = f"{random_name}.jpeg"
        image.filename = saved_file_name
        image = resize_image(image)

        save_dir = os.path.join(IMAGE_FILE_PATH, str(inquiry_seq))
        os.makedirs(save_dir, exist_ok=True)

        save_path = os.path.join(save_dir, saved_file_name)
    
        image.save(save_path, "jpeg", quality=70)

        stmt = insert(InquiryFile).values(
            inquiry_seq=inquiry_seq,
            file_name=file_name,
            saved_file_name=saved_file_name,
        ).returning(InquiryFile.inquiry_file_seq)
        result = await db.execute(stmt)
        inquiry_file_seq = result.scalar()
        success_image_seq_arr.append(inquiry_file_seq)

    result2 = True
    if len(images)>0:
        result2 = False
    if len(images) == len(success_image_seq_arr):
        result2 = True
    
    if inquiry_seq and result2:
        await db.commit()
        return make_resp("S")
    else:
        await db.rollback()
        return make_resp("E200")
