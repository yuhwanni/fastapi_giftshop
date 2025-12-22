from math import ceil
from typing import Optional
import secrets
import re
import random
import string
from sqlalchemy import select
from reward_app.models.member_model import Member
from reward_app.models.ads_complete_model import AdsComplete

from email_validator import validate_email, EmailNotValidError

from PIL import Image, ImageOps
from fastapi import UploadFile

def make_page_info(total_count: int, page: int = 1, size: int = 20):
    """
    페이징 정보 생성
    """
    total_pages = ceil(total_count / size) if total_count else 0

    # 마지막 페이지 여부
    is_last = page >= total_pages if total_pages > 0 else True

    # 이전 / 다음 페이지 번호
    previous_page: Optional[int] = page - 1 if page > 1 else None
    next_page: Optional[int] = page + 1 if page < total_pages else None

    return {
        "page": page,
        "size": size,
        "total_pages": total_pages,
        "total_count": total_count,
        "is_last": is_last,
        "previous_page": previous_page,
        "next_page": next_page
    }



def generate_secure_6digit_code():
    return str(secrets.randbelow(900000) + 100000)

def is_valid_phone_number(phone: str) -> bool:
    # 숫자만 남기기
    phone = re.sub(r'[^0-9]', '', phone)
    
    # 정규식 검사 (010, 011, 016~019로 시작하는 10~11자리)
    pattern = re.compile(r'^01[016789][0-9]{7,8}$')
    return bool(pattern.match(phone))

def generate_referral_code_random():
    """랜덤 영문 대문자 + 숫자 조합"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=10))


async def generate_unique_referral_code(db, max_attempts=10):
    """DB에서 중복 체크하면서 생성"""
    code = ''
    for _ in range(max_attempts):
        code = generate_referral_code_random()
        
        # 중복 체크
        stmt = select(Member).where(Member.referral_code == code)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            break
    
    return code

def generate_clickid_random():
    """랜덤 영문 대문자 + 숫자 조합"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=64))

async def generate_clickid(db, max_attempts=10):
    """DB에서 중복 체크하면서 생성"""
    clickid = ''
    result = False
    for _ in range(max_attempts):
        clickid = generate_clickid_random()
        
        # 중복 체크
        stmt = select(AdsComplete).where(AdsComplete.clickid == clickid)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            result = True
            break
    if not result:
        clickid=''

    return clickid



def is_valid_email(email: str) -> bool:
    try:
        validate_email(email)  # 유효성 + 정규화 수행
        return True
    except EmailNotValidError:
        return False

def is_valid_password(password: str) -> bool:
    # 8~20자리, 최소 하나의 영문자, 숫자, 특수문자 포함
    pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>_\-+=~`[\]\\;/])[A-Za-z\d!@#$%^&*(),.?":{}|<>_\-+=~`[\]\\;/]{8,20}$'
    return re.match(pattern, password) is not None

def resize_image(file: UploadFile, max_size: int = 1024):
    read_image = Image.open(file.file)
    original_width, original_height = read_image.size
 
    if original_width > max_size or original_height > max_size:
        if original_width > original_height:
            new_width = max_size
            new_height = int((new_width / original_width) * original_height)
        else:
            new_height = max_size
            new_width = int((new_height / original_height) * original_width)
        read_image = read_image.resize((new_width, new_height))
 
    read_image = read_image.convert("RGB")
    read_image = ImageOps.exif_transpose(read_image)
    return read_image
    