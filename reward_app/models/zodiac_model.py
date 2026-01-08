from sqlalchemy import (
    Column, String, Integer, BigInteger, Text, 
    Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Zodiac(Base):
    __tablename__ = "PC_ZODIAC"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="고유 ID")
    zodiac = Column(String(10), nullable=False, comment="별자리")
    weekday = Column(Integer, nullable=False, comment="요일 (0~6)")
    category = Column(String(10), nullable=False, comment="카테고리")
    variant = Column(Integer, nullable=False, comment="변형 타입")
    fortune = Column(Text, nullable=False, comment="운세 내용")

    __table_args__ = (
        UniqueConstraint(
            'zodiac', 'weekday', 'category', 'variant',
            name='uq_fixed'
        ),
        Index(
            'idx_lookup',
            'zodiac', 'weekday', 'category'
        ),
        Index(
            'idx_weekday_category',
            'weekday', 'category'
        ),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_general_ci',
            'comment': '별자리 요일별 운세 테이블'
        }
    )
