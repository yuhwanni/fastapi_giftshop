from sqlalchemy import Column, String, DateTime, Enum, text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class GiftishowGoods(Base):
    __tablename__ = "API_GIFTISHOW_GOODS"

    goodsCode = Column(String(20), nullable=False, primary_key=True, comment="상품 아이디")
    goodsNo = Column(String(10), nullable=True, comment="상품 번호")
    goodsName = Column(String(200), nullable=True, comment="상품명")
    brandCode = Column(String(20), nullable=True, comment="브랜드 코드")
    brandName = Column(String(200), nullable=True, comment="브랜드 명")
    content = Column(String(4000), nullable=True, comment="상품설명")
    contentAddDesc = Column(String(4000), nullable=True, comment="상품추가설명")
    discountRate = Column(String(10), nullable=True, comment="최종판매할인률")
    goodstypeNm = Column(String(20), nullable=True, comment="상품유형명")
    goodsImgS = Column(String(300), nullable=True, comment="상품이미지 소(250X250)")
    goodsImgB = Column(String(300), nullable=True, comment="상품이미지 대(500X500)")
    goodsDescImgWeb = Column(String(300), nullable=True, comment="상품 설명 이미지")
    brandIconImg = Column(String(300), nullable=True, comment="브랜드 아이콘 이미지")
    mmsGoodsImg = Column(String(300), nullable=True, comment="상품 MMS 이미지")
    discountPrice = Column(String(10), nullable=True, comment="최종판매가격")
    realPrice = Column(String(10), nullable=True, comment="실판매가격(등급별 할인율 적용금액)")
    salePrice = Column(String(10), nullable=True, comment="할인가")
    srchKeyword = Column(String(2000), nullable=True, comment="상품검색어")
    validPrdTypeCd = Column(String(2), nullable=True, comment="유효기간 유형(01-일수//02-일자)")
    limitday = Column(String(5), nullable=True, comment="유효기간(일자)")
    validPrdDay = Column(String(8), nullable=True, comment="유효기간(일수)")
    endDate = Column(DateTime, nullable=True, comment="판매종료일")
    goodsComId = Column(String(20), nullable=True, comment="상품공급사ID")
    goodsComName = Column(String(30), nullable=True, comment="상품공급사명")
    affiliateId = Column(String(20), nullable=True, comment="교환처ID")
    affilate = Column(String(30), nullable=True, comment="교환처명")
    exhGenderCd = Column(String(20), nullable=True, comment="전시성별코드")
    exhAgeCd = Column(String(20), nullable=True, comment="전시연령코드")
    mmsReserveFlag = Column(String(1), nullable=True, comment="예약발송노출여부")
    goodsStateCd = Column(String(20), nullable=True, comment="상품상태코드 (판매중: SALE, 판매중지: SUS)")
    mmsBarcdCreateYn = Column(String(50), nullable=True, comment="공급사 MMS 바코드 생성여부")
    rmCntFlag = Column(String(1), nullable=True, comment="총판매수량설정여부")
    saleDateFlagCd = Column(String(20), nullable=True, comment="판매일시 설정코드")
    goodsTypeDtlNm = Column(String(8), nullable=True, comment="상세상품유형명")
    category1Seq = Column(String(10), nullable=True, comment="전시카테고리1")
    saleDateFlag = Column(String(1), nullable=True, comment="판매일시설정여부")
    sellDisRate = Column(String(10), nullable=True, comment="공급할인")
    rmIdBuyCntFlagCd = Column(String(20), nullable=True, comment="ID당구매가능수량설정코드")
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    point_multi = Column(String(5), nullable=True, server_default=text("'4.4'"), comment="포인트로 상품구매시 realPrice*point_multi = 구매 필요 포인트")
    real_point = Column(String(20), nullable=True, comment="real_point 컬럼이 있을 경우 point_multi 보다 real_point가 우선")
    bylot_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="뽑기 상품 페이지 등록여부")
    bylot_point = Column(String(20), nullable=True, server_default=text("'91'"), comment="1회 뽑기에 필요한 포인트")
    bylot_type = Column(String(20), nullable=True, server_default=text("'bylot_percent'"), comment="뽑기 당첨 방식 bylot_percent 확률, bylot_n n번째마다 당첨")
    bylot_percent = Column(String(10), nullable=True, server_default=text("'0.002'"))
    bylot_n = Column(String(20), nullable=True, server_default=text("'2000'"))
    is_sale = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="상품 페이지 노출여부")
    is_naverpay = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"))
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"))
    upd_date = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_brandCode', 'brandCode'),
        Index('idx_goodsStateCd', 'goodsStateCd'),
        Index('idx_is_sale', 'is_sale'),
        Index('idx_bylot_yn', 'bylot_yn'),
    )