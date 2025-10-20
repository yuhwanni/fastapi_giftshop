from sqlalchemy import Column, String, Integer, DateTime, Enum, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Referral(Base):
    __tablename__ = "PC_REFERRAL"

    user_seq = Column(Integer, nullable=False, primary_key=True, comment="회원 순번 (추천받은 회원)")
    referrer_user_seq = Column(Integer, nullable=False, primary_key=True, comment="추천한 회원 순번")
    referral_datetime = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="추천시각")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    __table_args__ = (
        Index('idx_referrer_user_seq', 'referrer_user_seq'),
        Index('idx_referral_datetime', 'referral_datetime'),
        Index('idx_del_yn', 'del_yn'),
    )