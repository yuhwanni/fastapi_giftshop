from sqlalchemy import (
    Column, String, BigInteger, DateTime, Enum, text
)
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class GiftishowSend(Base):
    __tablename__ = "API_GIFTISHOW_SEND"

    order_no = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False, default=0, comment="주문번호")
    goods_code = Column(String(20), nullable=False, comment="상품코드")
    mms_msg = Column(String(1000), nullable=False, comment="MMS메시지")
    mms_title = Column(String(10), nullable=False, comment="MMS제목")
    callback_no = Column(String(12), nullable=False, comment="발신번호(- 제외)")
    phone_no = Column(String(12), nullable=False, comment="수신번호(- 제외)")
    tr_id = Column(String(25), nullable=False, comment="거래아이디 (Unique한 ID)")
    rev_info_yn = Column(String(1), nullable=True, default="N", comment="예약발송여부 (Y/N)")
    rev_info_date = Column(String(8), nullable=True, comment="예약일자 (yyyyMMdd)")
    rev_info_time = Column(String(4), nullable=True, comment="예약시간 (HHmm)")
    template_id = Column(String(10), nullable=True, comment="카드 아이디")
    banner_id = Column(String(10), nullable=True, comment="배너 아이디")
    user_id = Column(String(40), nullable=False, comment="회원 ID")
    gubun = Column(String(1), nullable=False, comment="MMS 발송 구분자 (Y/N/I)")

    code = Column(String(4), nullable=True, comment="결과코드")
    message = Column(String(50), nullable=True, comment="결과메시지")
    cancel_code = Column(String(4), nullable=True, comment="취소결과코드")
    cancel_message = Column(String(50), nullable=True, comment="취소결과메시지")
    pinNo = Column(String(20), nullable=True, comment="쿠폰번호")
    orderNo = Column(String(20), nullable=True, comment="주문번호")
    couponImgUrl = Column(String(255), nullable=True, comment="쿠폰 이미지 URL")

    detail_yn = Column(String(1), nullable=True, comment="상세정보확인 여부")

    brandNm = Column(String(100), nullable=True, comment="브랜드명")
    cnsmPriceAmt = Column(String(20), nullable=True, comment="정상판매단가")
    correcDtm = Column(String(8), nullable=True, comment="변경일자")
    goodsCd = Column(String(12), nullable=True, comment="상품코드")
    goodsNm = Column(String(100), nullable=True, comment="상품명")
    mmsBrandThumImg = Column(String(300), nullable=True, comment="브랜드 썸네일 이미지")
    recverTelNo = Column(String(11), nullable=True, comment="수신자번호")
    sellPriceAmt = Column(String(20), nullable=True, comment="실판매단가")
    sendBasicCd = Column(String(30), nullable=True, comment="기본번호")
    sendRstCd = Column(String(10), nullable=True, comment="거래번호")
    sendRstMsg = Column(String(10), nullable=True, comment="발송상태코드")
    sendStatusCd = Column(String(10), nullable=True, comment="발송상태명")
    senderTelNo = Column(String(11), nullable=True, comment="발신자번호")
    validPrdEndDt = Column(String(14), nullable=True, comment="유효기간만료일")
    pinStatusCd = Column(String(40), nullable=True, comment="핀상태코드")
    pinStatusNm = Column(String(40), nullable=True, comment="핀상태명")

    crt_date = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    upd_date = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
