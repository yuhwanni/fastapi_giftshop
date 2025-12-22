from sqlalchemy import Column, String, Integer, DateTime, Enum, text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Ads(Base):
    __tablename__ = "PC_ADS"

    ads_id = Column(Integer, nullable=False, primary_key=True, comment="광고키")
    ads_name = Column(String(255), nullable=False, server_default=text("''"), comment="광고명")
    ads_title = Column(String(255), nullable=True, comment="캠페인 타이틀")
    ads_condition = Column(String(255), nullable=True, comment="캠페인 달성조건")
    
    ads_feed_img = Column(String(255), nullable=True, comment="캠페인 피드 이미지")
    ads_reward_price = Column(Integer, nullable=True, comment="단가")
    ads_order = Column(Integer, nullable=True, comment="순번")
    ads_os_type = Column(Enum('A', 'I', 'W', 'ALL'), nullable=False, server_default=text("'ALL'"), comment="os type")
    show_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'Y'"), comment="노출상태")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="등록일")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")
    ads_type = Column(String(2), nullable=True, comment="캠페인 타입코드")
    