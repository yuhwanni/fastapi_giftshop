from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Enum, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Refund(Base):
    __tablename__ = "PC_REFUND"

    refund_seq = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, comment="환급 순번")
    user_seq = Column(Integer, nullable=False, comment="사용자 순번")
    refund_amount = Column(Integer, nullable=False, comment="신청 금액")
    bank_name = Column(String(50), nullable=False, comment="은행명")
    account_number = Column(String(50), nullable=False, comment="계좌번호")
    account_holder = Column(String(50), nullable=False, comment="예금주")
    refund_status = Column(Enum('R', 'C', 'P', 'M', 'J'), nullable=False, server_default=text("'R'"), comment="환급상태 (R:신청완료, C:신청취소, P:처리중, M:환급완료, J:환급불가)")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    __table_args__ = (
        Index('idx_user_seq', 'user_seq'),
        Index('idx_refund_status', 'refund_status'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
    )