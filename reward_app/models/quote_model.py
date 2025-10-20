from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Enum, Text, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Quote(Base):
    __tablename__ = "PC_QUOTE"

    quote_seq = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, comment="명언 순번")
    person_name = Column(String(100), nullable=False, comment="인물명")
    content = Column(Text, nullable=False, comment="내용")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")
    
    __table_args__ = (
        Index('idx_person_name', 'person_name'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
    )


Base = declarative_base()

class QuoteLike(Base):
    __tablename__ = "PC_QUOTE_LIKE"
    __table_args__ = (
        Index('idx_unique_like', 'quote_seq', 'user_seq', 'del_yn', unique=True),
        Index('idx_quote_seq', 'quote_seq'),
        Index('idx_user_seq', 'user_seq'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
    )

    quote_seq = Column(BigInteger, nullable=False, primary_key=True, comment="명언 순번 (PC_QUOTE 참조)")
    user_seq = Column(Integer, nullable=False, primary_key=True, comment="회원 순번")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

