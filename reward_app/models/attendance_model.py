from sqlalchemy import Column, String, Integer, Date, DateTime, Enum, text, Index, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Attendance(Base):
    __tablename__ = "PC_ATTENDANCE"

    attendance_seq = Column(Integer, primary_key=True, autoincrement=True, comment="출석 순번")
    user_seq = Column(Integer, nullable=False, comment="회원 순번")
    attendance_date = Column(Date, nullable=False, comment="출석일 (YYYY-MM-DD)")
    point = Column(Integer, nullable=False, server_default=text("0"), comment="적립포인트")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    __table_args__ = (
        UniqueConstraint('user_seq', 'attendance_date', name='user_seq_attendance_date'),
        Index('idx_attendance_date', 'attendance_date'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
        {'comment': '출석 체크 테이블', 'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'}
    )