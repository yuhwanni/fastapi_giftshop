from sqlalchemy import select, insert, update, delete, func, between, and_, text

import json
from reward_app.models.member_model import Member
from reward_app.models.point_history_model import PointHistory
from sqlalchemy.ext.asyncio import AsyncSession
import inspect


async def save_point(db: AsyncSession, user_seq:int, point_name:str, point:int=0, table_name:str="", table_seq:int=0, point_type:str=""):    
    
    stmt = insert(PointHistory).values(
        user_seq = user_seq,
        point_name = point_name,
        point = point,
        earn_use_type = "E",
        point_type = point_type,
        table_name = table_name,
        table_seq = table_seq
    )
    result2 = await db.execute(stmt)
    
    stmt = update(Member).where(Member.user_seq==user_seq).values(
        user_point = Member.user_point+point,
    )
    result3 = await db.execute(stmt)
    # await db.commit()

    result = False
    if result2 and result3:
        await db.commit()
        result = True
    else:
        await db.rollback()
    # if callback:
    #     try:
    #         if inspect.iscoroutinefunction(callback):
    #             await callback(result)
    #         else:
    #             callback(result)
    #     except Exception as e:
    #         print(f"⚠️ 콜백 실행 중 오류: {e}")

    return result

async def reduce_point(db: AsyncSession, user_seq:int, point_name:str, point:int=0, table_name:str="", table_seq:int=0, point_type:str=""):    
    
    member_stmt = select(Member).where(Member.user_seq==user_seq)
    member_result = await db.execute(member_stmt)
    member = member_result.scalars().first()
    user_point = member.user_point

    if user_point < point:
        return False

    stmt = insert(PointHistory).values(
        user_seq = user_seq,
        point_name = point_name,
        point = point,
        earn_use_type = "U",
        point_type = point_type,
        table_name = table_name,
        table_seq = table_seq
    )
    result2 = await db.execute(stmt)
    
    stmt = update(Member).where(Member.user_seq==user_seq).values(
        user_point = Member.user_point-point,
    )
    result3 = await db.execute(stmt)
    # await db.commit()

    result = False
    if result2 and result3:
        await db.commit()
        result = True
    else:
        await db.rollback()
    # if callback:
    #     try:
    #         if inspect.iscoroutinefunction(callback):
    #             await callback(result)
    #         else:
    #             callback(result)
    #     except Exception as e:
    #         print(f"⚠️ 콜백 실행 중 오류: {e}")

    return result