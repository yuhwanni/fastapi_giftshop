from sqlalchemy import Column, String, DateTime, Enum, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AuthVerify(Base):
    __tablename__ = "PC_AUTH_VERIFY"

    auth_token = Column(String(64), nullable=False, primary_key=True, comment="가입 토큰")
    phone = Column(String(20), nullable=True, comment="전화번호")
    device_id = Column(String(64), nullable=False, primary_key=True, comment="디바이스 아이디")
    verify_code = Column(String(6), nullable=True, comment="인증번호")
    user_email = Column(String(255), nullable=True, comment="이메일. 비밀번호변경시 사용")
    expire_date = Column(DateTime, nullable=True, comment="인증기한")
    verify_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="인증완료여부")
    verify_date = Column(DateTime, nullable=True, comment="인증완료일")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")

    __table_args__ = (
        Index('idx_phone', 'phone'),
        Index('idx_crt_date', 'crt_date'),
    )