from sqlalchemy import Column, String, BigInteger, DateTime, Text, text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SmsHistory(Base):
    __tablename__ = "PC_SMS_HISTORY"

    sms_seq = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, comment="문자 아이디 (PK)")
    user_seq = Column(BigInteger, nullable=True, comment="고객 아이디")
    receive_number = Column(String(20), nullable=False, comment="수신 번호")
    send_number = Column(String(20), nullable=False, comment="발신번호")
    subject = Column(String(255), nullable=True, comment="제목")
    message = Column(Text, nullable=False, comment="내용")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    crt_id = Column(String(20), nullable=True)
    upd_id = Column(String(20), nullable=True)
    result_code = Column(String(50), nullable=True)
    result_description = Column(String(100), nullable=True)
    result_messagekey = Column(String(100), nullable=True)