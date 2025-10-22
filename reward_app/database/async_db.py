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

from reward_app.utils.log_util import db_logger as logger
import traceback

load_dotenv()


# -----------------------------
# 환경 변수
# -----------------------------
DB_USER = os.getenv("DB_USER2")
DB_PASS = os.getenv("DB_PASS2")
DB_HOST = os.getenv("DB_HOST2", "localhost")
DB_PORT = os.getenv("DB_PORT2", "3306")
DB_NAME = os.getenv("DB_NAME2")

# -----------------------------
# AsyncDatabase
# -----------------------------
class AsyncDatabase:
    def __init__(self):
        self.database_url = (
            f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
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
                echo=False,
                pool_pre_ping=True,        # 연결 검증
                pool_recycle=1800,         # 30분마다 재생성
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
    await async_db._ensure_initialized()
    async with async_db.async_session() as session:
        # yield session
        try:
            yield session
        except Exception as e:    # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.error(f"DB Error: {e}")    
            err_msg = traceback.format_exc()
            logger.error(err_msg)    
        finally:
            await session.close()


# -----------------------------
# 싱글톤 인스턴스
# -----------------------------
async_db = AsyncDatabase()

def get_async_db():
    return async_db