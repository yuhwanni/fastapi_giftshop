from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Enum, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AdsComplete(Base):
    __tablename__ = "PC_ADS_COMPLETE"

    complete_seq = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, comment="광고 참여완료 순번")
    clickid = Column(String(64), nullable=False, comment="클릭 아이디")
    ads_id = Column(String(100), nullable=False, comment="광고 아이디")
    ads_name = Column(String(200), nullable=False, comment="광고명")
    user_seq = Column(Integer, nullable=False, comment="사용자 순번")
    adid = Column(String(100), nullable=False, comment="ADID or IDFA")
    payout = Column(Integer, nullable=False, server_default=text("0"), comment="매체 단가")
    user_cost = Column(Integer, nullable=False, server_default=text("0"), comment="유저 리워드")
    unq_campaign = Column(Enum('Y', 'N'), nullable=False, server_default=text("'N'"), comment="중복지급가능여부")
    point_add_yn = Column(Enum('Y', 'N'), nullable=False, server_default=text("'N'"), comment="포인트 지급여부")
    complete_yn = Column(Enum('Y', 'N'), nullable=False, server_default=text("'N'"), comment="광고참여 완료여부")
    host_ip = Column(String(50), nullable=False, server_default=text("''"), comment="host ip")
    join_ip = Column(String(50), nullable=False, server_default=text("''"), comment="join_ip")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="생성일")
    crt_id = Column(String(50), nullable=True, comment="생성자 아이디")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    upd_id = Column(String(50), nullable=True, comment="수정자 아이디")
    del_date = Column(DateTime, nullable=True, comment="삭제일")
    del_id = Column(String(50), nullable=True, comment="삭제자 아이디")
    del_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="삭제여부")

    __table_args__ = (
        Index('idx_ads_id', 'ads_id'),
        Index('idx_user_seq', 'user_seq'),
        Index('idx_adid', 'adid'),
        Index('idx_del_yn', 'del_yn'),
        Index('idx_crt_date', 'crt_date'),
    )