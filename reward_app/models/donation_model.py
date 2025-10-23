from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Enum, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Donation(Base):
    __tablename__ = "PC_DONATION"

    donation_seq = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, comment="기부 순번")
    user_seq = Column(Integer, nullable=False, comment="사용자 순번")
    donation_point = Column(Integer, nullable=False, comment="기부 포인트")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    __table_args__ = (
        Index('idx_user_seq', 'user_seq'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
    )