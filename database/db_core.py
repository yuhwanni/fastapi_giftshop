import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

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
# 공통 환경 변수
# -----------------------------
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME")

# -----------------------------
# 비동기 MariaDB Database
# -----------------------------
class AsyncDatabase:
    def __init__(self):
        self.database_url = f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        self.engine = create_async_engine(self.database_url, echo=False, future=True)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        # logger.info("AsyncDatabase engine created.")

    @asynccontextmanager
    async def transaction(self):
        session = self.async_session()
        try:
            yield session
            await session.commit()
            # logger.info("Async transaction committed.")
        except Exception as e:
            await session.rollback()
            # logger.error(f"Async transaction rollback: {e}")
            raise
        finally:
            await session.close()

    async def execute(self, query, params=None):
        async with self.async_session() as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result

    async def fetchall(self, query, params=None):
        try:
            async with self.async_session() as session:
                result = await session.execute(text(query), params or {})
                return [dict(row) for row in result.mappings()]
        except Exception as e:
            print(e)

    async def fetchone(self, query, params=None):
        async with self.async_session() as session:
            result = await session.execute(text(query), params or {})
            row = result.mappings().first()
            return dict(row) if row else None

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
        async with self.transaction() as session:
            await session.execute(text(query), data_list)

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
# sync_db = SyncDatabase()
async_db = AsyncDatabase()

def get_async_db():
    return async_db    