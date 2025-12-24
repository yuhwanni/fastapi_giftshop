from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Enum, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class PointHistory(Base):
    __tablename__ = "PC_POINT_HISTORY"

    point_seq = Column(BigInteger, primary_key=True, autoincrement=True, comment="포인트 내역 순번")
    user_seq = Column(Integer, nullable=False, comment="사용자 순번")
    point_name = Column(String(100), nullable=False, comment="포인트명")
    point = Column(Integer, nullable=False, comment="포인트")
    earn_use_type = Column(Enum('E', 'U'), nullable=False, comment="적립/사용 구분 (E:적립, U:사용)")
    point_type = Column(Enum('E', 'A', 'T', 'Q', 'G', 'D', 'R', 'J', 'JA', 'I'), nullable=False, server_default=text("'E'"), comment="포인트타입 (E:기타 , A:광고, T:출석체크, Q:퀴즈, G:기프트샵, D:기부, R:환급, J:가입, JA:추천으로 가입후 첫광고완료, I:추천)")
    table_name = Column(String(20), nullable=False, server_default=text("''"), comment="테이블명")
    table_seq = Column(Integer, nullable=False, server_default=text("0"), comment="테이블 순번")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    __table_args__ = (
        Index('idx_user_seq', 'user_seq'),
        Index('idx_earn_use_type', 'earn_use_type'),
        Index('idx_point_type', 'point_type'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
        {'comment': '포인트 내역 테이블', 'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'}
    )