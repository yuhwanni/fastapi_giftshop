from sqlalchemy import Column, String, Integer, DateTime, Enum, text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Ads(Base):
    __tablename__ = "PC_ADS"

    campaign_id = Column(Integer, nullable=False, primary_key=True, comment="광고키")
    campaign_name = Column(String(255), nullable=False, server_default=text("''"), comment="광고명")
    campaign_title = Column(String(255), nullable=True, comment="캠페인 타이틀")
    campaign_feed_img = Column(String(255), nullable=True, comment="캠페인 피드 이미지")
    campaign_reward_price = Column(Integer, nullable=True, comment="단가")
    campaign_os_type = Column(Enum('A', 'I', 'W', 'ALL'), nullable=False, server_default=text("'ALL'"), comment="os type")
    show_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'Y'"), comment="노출상태")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), comment="등록일")
    upd_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"), onupdate=text("current_timestamp()"), comment="수정일")