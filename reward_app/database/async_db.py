import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError, InterfaceError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
import asyncio

from fastapi import HTTPException

from reward_app.utils.log_util import db_logger as logger
import traceback

load_dotenv()


# -----------------------------
# 환경 변수
# -----------------------------
GIFT_DB_USER = os.getenv("DB_USER")
GIFT_DB_PASS = os.getenv("DB_PASS")
GIFT_DB_HOST = os.getenv("DB_HOST", "localhost")
GIFT_DB_PORT = os.getenv("DB_PORT", "3306")
GIFT_DB_NAME = os.getenv("DB_NAME")

REWARD_DB_USER = os.getenv("DB_USER2")
REWARD_DB_PASS = os.getenv("DB_PASS2")
REWARD_DB_HOST = os.getenv("DB_HOST2", "localhost")
REWARD_DB_PORT = os.getenv("DB_PORT2", "3306")
REWARD_DB_NAME = os.getenv("DB_NAME2")

# -----------------------------
# AsyncDatabase
# -----------------------------
class AsyncDatabase:
    def __init__(self, db_user, db_pass, db_host, db_port, db_name):
        self.database_url = (
            f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            f"?charset=utf8mb4"
        )
        self.engine = None
        self.async_session = None
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def _initialize(self):
        """엔진과 세션 초기화"""
        async with self._init_lock:
            if self._initialized:
                return
            
            self.engine = create_async_engine(
                self.database_url,
                echo=True,
                pool_pre_ping=True,        # 연결 검증
                pool_recycle=6,         # 30분마다 재생성
                pool_timeout=30,           # 풀 대기 타임아웃
                pool_size=5,               # 기본 풀 크기
                max_overflow=10,           # 추가 연결 허용
                pool_reset_on_return='rollback',
                connect_args={
                    "connect_timeout": 10,
                    "autocommit": False,
                    "charset": "utf8mb4",
                },
            )
            
            self.async_session = async_sessionmaker(
                self.engine, 
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,                
            )
            
            self._initialized = True
            logger.info("✅ AsyncDatabase 초기화 완료")

    async def _ensure_initialized(self):
        """초기화 보장"""
        if not self._initialized:
            await self._initialize()

    async def health_check(self):
        """헬스체크"""
        try:
            async with self.async_session() as session:
                result = await session.execute(text("SELECT 1 as health"), {})
                result = dict(result.mappings().first())
                if result and result.get('health') == 1:
                    logger.info("✅ DB 헬스체크 통과")
                    return True
        except Exception as e:
            logger.error(f"❌ DB 헬스체크 실패: {e}")
            return False
        return False

    async def get_pool_status(self):
        """연결 풀 상태"""
        if not self.engine:
            return {"status": "초기화 안됨"}
        
        pool = self.engine.pool
        return {
            "total_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "status": "정상" if pool.checkedin() > 0 else "경고"
        }

    async def close(self):
        """엔진 종료"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("✅ AsyncDatabase 종료")


# FastAPI 의존성 주입용
async def get_async_session():
    await reward_db._ensure_initialized()
    async with reward_db.async_session() as session:
        # yield session
        try:
            yield session
        # except HTTPException:
        #     # HTTPException은 FastAPI가 처리하도록 그대로 전파
        #     raise    
        except (SQLAlchemyError, OperationalError, InterfaceError) as e:
            logger.error(f"DB Error: {e}")    
            err_msg = traceback.format_exc()
            logger.error(err_msg)    
        finally:
            await session.close()

async def get_async_gift_session():
    await gift_db._ensure_initialized()
    async with gift_db.async_session() as session:
        # yield session
        try:
            yield session
        # except HTTPException:
        #     # HTTPException은 FastAPI가 처리하도록 그대로 전파
        #     raise  
        except (SQLAlchemyError, OperationalError, InterfaceError) as e:
            logger.error(f"GIFT DB Error: {e}")    
            err_msg = traceback.format_exc()
            logger.error(err_msg)    
        finally:
            await session.close()

# -----------------------------
# 싱글톤 인스턴스
# -----------------------------
reward_db = AsyncDatabase(REWARD_DB_USER, REWARD_DB_PASS, REWARD_DB_HOST, REWARD_DB_PORT, REWARD_DB_NAME)
gift_db = AsyncDatabase(GIFT_DB_USER, GIFT_DB_PASS, GIFT_DB_HOST, GIFT_DB_PORT, GIFT_DB_NAME)


def get_async_db():
    return reward_db