from sqlalchemy import Column, String, Integer, Date, DateTime, Enum, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Attendance(Base):
    __tablename__ = "PC_ATTENDANCE"

    user_seq = Column(Integer, nullable=False, primary_key=True, comment="회원 순번")
    attendance_date = Column(Date, nullable=False, primary_key=True, comment="출석일 (YYYY-MM-DD)")
    point = Column(Integer, nullable=False, server_default=text("0"), comment="적립포인트")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    __table_args__ = (
        Index('idx_attendance_date', 'attendance_date'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
    )