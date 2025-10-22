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

load_dotenv()

# -----------------------------
# 로그 설정
# -----------------------------
today_str = datetime.now().strftime("%Y%m%d")
log_dir = os.path.join("logs", today_str)
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "database.log")

logger = logging.getLogger("DatabaseLogger")
logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# -----------------------------
# 환경 변수
# -----------------------------
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

# -----------------------------
# AsyncDatabase
# -----------------------------
class AsyncDatabase:
    def __init__(self):
        self.database_url = f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        self.engine = None
        self.async_session = None
        asyncio.create_task(self._initialize())

    async def _initialize(self):
        """엔진과 세션 초기화"""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,  # 💡 DB 연결 확인 후 재사용
            pool_recycle=6,   # 💡 1시간마다 커넥션 재생성
            future=True
        )
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        logger.info("✅ AsyncDatabase engine initialized.")

    async def _reconnect(self):
        """연결이 끊긴 경우 재연결"""
        logger.warning("⚠️  Database connection lost. Trying to reconnect...")
        await asyncio.sleep(1)
        await self._initialize()

    @asynccontextmanager
    async def transaction(self):
        """트랜잭션"""
        session = self.async_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async transaction rollback: {e}")
            raise
        finally:
            await session.close()

    async def _execute_with_reconnect(self, func, *args, **kwargs):
        """공통: 연결 끊김 시 재시도 래퍼"""
        try:
            return await func(*args, **kwargs)
        except (OperationalError, InterfaceError) as e:
            logger.warning(f"DB connection error: {e}. Retrying...")
            await self._reconnect()
            # 재시도
            return await func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error: {e}")
            raise

    async def execute(self, query, params=None):
        async def _exec():
            async with self.async_session() as session:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result

        return await self._execute_with_reconnect(_exec)

    async def fetchall(self, query, params=None):
        async def _fetch():
            async with self.async_session() as session:
                result = await session.execute(text(query), params or {})
                return [dict(row) for row in result.mappings()]

        return await self._execute_with_reconnect(_fetch)

    async def fetchone(self, query, params=None):
        async def _fetch_one():
            async with self.async_session() as session:
                result = await session.execute(text(query), params or {})
                row = result.mappings().first()
                return dict(row) if row else None

        return await self._execute_with_reconnect(_fetch_one)

    async def insert_one(self, table, data: dict):
        cols = ", ".join(data.keys())
        vals = ", ".join([f":{k}" for k in data.keys()])
        query = f"INSERT INTO {table} ({cols}) VALUES ({vals})"
        await self.execute(query, data)

    async def insert_many(self, table, data_list: list[dict], update_on_duplicate=False):
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
        await self._execute_with_reconnect(_insert_many)

    async def update(self, query, params=None):
        await self.execute(query, params)

    async def delete(self, query, params=None):
        await self.execute(query, params)

    async def create_table(self, table_name, columns_sql):
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_sql}
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci
        """
        await self.execute(query)


async def get_async_session() -> AsyncSession:
    async with async_db.async_session() as session:
        yield session


# -----------------------------
# 모듈 레벨 객체
# -----------------------------
async_db = AsyncDatabase()

def get_async_db():
    return async_db
