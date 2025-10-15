from sqlalchemy import Column, String, BigInteger, DateTime, text, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Brand(Base):
    __tablename__ = "API_GIFTISHOW_BRANDS"

    brandSeq = Column(String(10), nullable=True, comment="브랜드 일련번호")
    brandCode = Column(String(50), nullable=False, primary_key=True, comment="브랜드 코드")
    brandName = Column(String(50), nullable=True, comment="브랜드 명")
    brandBannerImg = Column(String(100), nullable=True, comment="웹배너 이미지")
    brandIconImg = Column(String(300), nullable=True, comment="브랜드아이콘 이미지")
    mmsThumImg = Column(String(300), nullable=True, comment="브랜드썸네일 이미지")
    content = Column(String(4000), nullable=True, comment="브랜드 설명")
    category1Name = Column(String(200), nullable=True, comment="카테고리1 명")
    category1Seq = Column(String(10), nullable=True, comment="카테고리1 일련번호")
    category2Name = Column(String(200), nullable=True, comment="카테고리2 명")
    category2Seq = Column(String(10), nullable=True, comment="카테고리2 일련번호")
    sort = Column(String(10), nullable=True, comment="정렬")
    crt_date = Column(DateTime, server_default=text("current_timestamp()"))
    upd_date = Column(DateTime, nullable=True)
    goods_cnt = Column(Integer, nullable=True, default=0, comment="상품수")
    
