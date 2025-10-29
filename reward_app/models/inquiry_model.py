from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Enum, Text, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Inquiry(Base):
    __tablename__ = "PC_INQUIRY"

    inquiry_seq = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, comment="문의 순번")
    user_seq = Column(Integer, nullable=False, comment="사용자 순번")
    title = Column(String(200), nullable=False, comment="제목")
    content = Column(Text, nullable=False, comment="내용")
    answer = Column(Text, nullable=True, comment="답변")
    file_cnt = Column(Integer, nullable=False, comment="파일첨부수")
    answer_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="N: 답변대기,Y: 답변완료")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    __table_args__ = (
        Index('idx_user_seq', 'user_seq'),
        Index('idx_answer_yn', 'answer_yn'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
    )


class InquiryFile(Base):
    __tablename__ = "PC_INQUIRY_FILE"

    inquiry_file_seq = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, comment="문의 첨부파일 순번")
    inquiry_seq = Column(BigInteger, nullable=False, comment="문의 순번")
    file_name = Column(String(255), nullable=False, comment="첨부파일명")
    saved_file_name = Column(String(255), nullable=False, comment="저장파일명")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    __table_args__ = (
        Index('idx_inquiry_seq', 'inquiry_seq'),
        Index('idx_del_yn', 'del_yn'),
    )