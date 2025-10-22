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

    async def _reconnect(self):
        """연결 재시도"""
        logger.warning("⚠️  DB 연결 끊김 감지. 재연결 시도 중...")
        
        if self.engine:
            try:
                await asyncio.wait_for(self.engine.dispose(), timeout=5.0)
                logger.info("기존 엔진 정리 완료")
            except asyncio.TimeoutError:
                logger.warning("엔진 정리 타임아웃")
            except Exception as e:
                logger.error(f"엔진 정리 중 오류: {e}")
        
        self._initialized = False
        self.engine = None
        self.async_session = None
        
        await asyncio.sleep(2)
        await self._initialize()
        logger.info("✅ 재연결 성공")

    @asynccontextmanager
    async def transaction(self):
        """트랜잭션 컨텍스트"""
        await self._ensure_initialized()
        session = self.async_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"트랜잭션 롤백: {e}")
            raise
        finally:
            await session.close()

    async def _execute_with_retry(self, func, max_retries=3):
        """재시도 로직"""
        await self._ensure_initialized()
        
        for attempt in range(1, max_retries + 1):
            try:
                return await func()
            except (OperationalError, InterfaceError, RuntimeError) as e:
                error_msg = str(e).lower()
                
                # 연결 끊김 관련 에러만 재시도
                should_retry = any(keyword in error_msg for keyword in [
                    'closed', 'lost connection', 'connection', 'timeout', 
                    'broken pipe', 'reset by peer'
                ])
                
                if not should_retry or attempt >= max_retries:
                    logger.error(f"최대 재시도 횟수 도달 ({attempt}/{max_retries}): {e}")
                    raise
                
                logger.warning(f"DB 오류 발생 (시도 {attempt}/{max_retries}): {type(e).__name__}")
                await self._reconnect()
                await asyncio.sleep(attempt)  # 점진적 대기
                
            except Exception as e:
                logger.error(f"예상치 못한 오류: {type(e).__name__}: {e}")
                raise

    async def execute(self, query, params=None):
        """쿼리 실행 (INSERT, UPDATE, DELETE)"""
        async def _exec():
            async with self.async_session() as session:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result
        
        return await self._execute_with_retry(_exec)

    async def fetchall(self, query, params=None):
        """여러 행 조회"""
        async def _fetch():
            async with self.async_session() as session:
                result = await session.execute(text(query), params or {})
                return [dict(row) for row in result.mappings()]
        
        return await self._execute_with_retry(_fetch)

    async def fetchone(self, query, params=None):
        """단일 행 조회"""
        async def _fetch_one():
            async with self.async_session() as session:
                result = await session.execute(text(query), params or {})
                row = result.mappings().first()
                return dict(row) if row else None
        
        return await self._execute_with_retry(_fetch_one)

    async def insert_one(self, table, data: dict):
        """단일 행 삽입"""
        cols = ", ".join(data.keys())
        vals = ", ".join([f":{k}" for k in data.keys()])
        query = f"INSERT INTO {table} ({cols}) VALUES ({vals})"
        await self.execute(query, data)

    async def insert_many(self, table, data_list: list[dict], update_on_duplicate=False):
        """다중 행 삽입"""
        if not data_list:
            return
        
        cols = ", ".join(data_list[0].keys())
        vals = ", ".join([f":{k}" for k in data_list[0].keys()])
        query = f"INSERT INTO {table} ({cols}) VALUES ({vals})"
        
        if update_on_duplicate:
            updates = ", ".join([f"{k}=VALUES({k})" for k in data_list[0].keys()])
            query += f" ON DUPLICATE KEY UPDATE {updates}"
        
        async def _insert_many():
            async with self.transaction() as session:
                await session.execute(text(query), data_list)
        
        await self._execute_with_retry(_insert_many)

    async def update(self, query, params=None):
        """업데이트"""
        await self.execute(query, params)

    async def delete(self, query, params=None):
        """삭제"""
        await self.execute(query, params)

    async def create_table(self, table_name, columns_sql):
        """테이블 생성"""
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_sql}
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
        """
        await self.execute(query)

    async def health_check(self):
        """헬스체크"""
        try:
            result = await self.fetchone("SELECT 1 as health")
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
        yield session


# -----------------------------
# 싱글톤 인스턴스
# -----------------------------
async_db = AsyncDatabase()

def get_async_db():
    return async_db