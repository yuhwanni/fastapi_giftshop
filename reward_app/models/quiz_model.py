from sqlalchemy import Column, String, BigInteger, Integer, Date, DateTime, Enum, text, Index, select, and_, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import date

Base = declarative_base()

class Quiz(Base):
    __tablename__ = "PC_QUIZ"

    quiz_seq = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, comment="퀴즈 순번")
    quiz = Column(String(500), nullable=False, comment="퀴즈")
    answer = Column(String(200), nullable=False, comment="정답")
    hint = Column(String(500), nullable=True, comment="힌트")
    reward_point = Column(Integer, nullable=False, server_default=text("0"), comment="적립포인트")
    start_date = Column(Date, nullable=False, comment="퀴즈시작일")
    end_date = Column(Date, nullable=False, comment="퀴즈종료일")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    # 1:1 Relationship
    # quiz_join = relationship("QuizJoin", back_populates="quiz", uselist=False)
    # quiz_join = relationship("QuizJoin", back_populates="quiz", uselist=False)

    __table_args__ = (
        Index('idx_start_date', 'start_date'),
        Index('idx_end_date', 'end_date'),
        Index('idx_del_yn', 'del_yn'),
    )

class QuizJoin(Base):
    __tablename__ = "PC_QUIZ_JOIN"

    quiz_seq = Column(BigInteger, nullable=False, primary_key=True, comment="퀴즈 순번 (PC_QUIZ 참조)")
    user_seq = Column(Integer, nullable=False, primary_key=True, comment="회원 순번")
    submit_answer = Column(String(200), nullable=False, comment="제출정답")
    is_correct = Column(Enum('Y', 'N'), nullable=False, comment="정답여부")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    # 1:1 Relationship
    # quiz = relationship("Quiz", back_populates="quiz_join")
    # quiz = relationship("QuizModel", back_populates="quiz_join", primaryjoin="Quiz.quiz_seq==QuizJoin.quiz_seq")

    __table_args__ = (
        Index('idx_user_seq', 'user_seq'),
        Index('idx_is_correct', 'is_correct'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
    )
