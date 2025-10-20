from sqlalchemy import Column, String, BigInteger, DateTime, Enum, Text, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Notice(Base):
    __tablename__ = "PC_NOTICE"

    notice_seq = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, comment="공지사항 순번")
    title = Column(String(200), nullable=False, comment="제목")
    content = Column(Text, nullable=False, comment="내용")
    is_top = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="최상단여부")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    __table_args__ = (
        Index('idx_is_top', 'is_top'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
    )
