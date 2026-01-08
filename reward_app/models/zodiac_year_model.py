from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ZodiacYear(Base):
    __tablename__ = "PC_ZODIAC_YEAR"

    zodiac = Column(String(10), primary_key=True, comment="별자리")
    examples = Column(String(50), nullable=False, comment="해당 별자리 연도 예시")

    __table_args__ = (
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_general_ci',
            'comment': '별자리 연도 매핑 테이블'
        },
    )
