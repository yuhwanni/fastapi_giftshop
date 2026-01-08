from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form
from fastapi.responses import RedirectResponse


from typing import List, Optional

from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.ext.asyncio import AsyncSession
from reward_app.database.async_db import get_async_session
import bcrypt

from sqlalchemy import select, insert,update,func, and_, text

from sqlalchemy import desc, asc


from reward_app.models.zodiac_model import Zodiac
from reward_app.models.zodiac_year_model import ZodiacYear
from reward_app.models.member_model import Member
from reward_app.core.config import make_resp
from reward_app.utils.params import DuplicateYn
from reward_app.service.point_service import save_point
from reward_app.models.ads_model import Ads
from reward_app.utils.log_util import api_logger

from reward_app.core.security import get_current_user

from reward_app.utils.common import generate_clickid

from reward_app.models.ads_complete_model import AdsComplete
from reward_app.utils.common import make_page_info
import httpx
from fastapi import HTTPException


router = APIRouter()


@router.post("/list", name="운세", description='''
''')
async def unse( 
    # , aff_key: str =Form()
    db: AsyncSession = Depends(get_async_session)
    ):  

    qry = """
    SELECT P.zodiac, P.fortune, PY.examples AS years
    FROM PC_ZODIAC P
    INNER JOIN PC_ZODIAC_YEAR PY ON (P.zodiac = PY.zodiac)
    WHERE P.weekday = DAYOFWEEK(CURDATE()) - 1
    AND P.category = :category
    AND P.variant = :variant
    """
    paged_results = await db.execute(text(qry), {"category": "종합", "variant": 1})

    list = [dict(row) for row in paged_results.mappings()]

    return make_resp("S", { "list":list})

    '''
    SELECT
  zodiac,
  GROUP_CONCAT(
    CONCAT(fortune)
    ORDER BY variant
    SEPARATOR '\t'
  ) AS fortunes
FROM PC_HOROSCOPE_ZODIAC
WHERE weekday = DAYOFWEEK(CURDATE()) - 1
  AND category = '종합'
  AND variant IN (1,2,3)
GROUP BY zodiac;
    '''