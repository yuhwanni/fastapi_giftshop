from math import ceil
from typing import Optional
import secrets

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
