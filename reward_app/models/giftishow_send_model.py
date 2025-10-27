from sqlalchemy import Column, String, BigInteger, DateTime, Enum, text, Index, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class GiftishowSend(Base):
    __tablename__ = "API_GIFTISHOW_SEND"

    order_no = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True, comment="주문번호")
    user_seq = Column(Integer, nullable=False, comment="회원번호")
    goods_code = Column(String(20), nullable=False, comment="상품코드")
    mms_msg = Column(String(1000), nullable=False, comment="MMS메시지")
    mms_title = Column(String(20), nullable=False, comment="MMS제목")
    callback_no = Column(String(12), nullable=False, comment="- 를 제외 발신번호")
    phone_no = Column(String(12), nullable=False, comment="- 를 제외한 수신번호")
    tr_id = Column(String(25), nullable=False, comment="거래아이디 (Unique한 ID) 고객사와 기프티쇼비즈간 대사값 (사용자생성 TR_ID)")
    rev_info_yn = Column(String(1), nullable=True, comment="예약발송여부 (Y:예약, N:실시간)")
    rev_info_date = Column(String(8), nullable=True, comment="예약일자 (yyyyMMdd)")
    rev_info_time = Column(String(4), nullable=True, comment="예약시간 (HHmm)")
    template_id = Column(String(10), nullable=True, comment="카드 아이디")
    banner_id = Column(String(10), nullable=True, comment="배너 아이디")
    user_id = Column(String(40), nullable=False, comment="회원 ID")
    gubun = Column(String(1), nullable=False, comment="MMS발송 구분자 - Y: 핀번호수신 - N: MMS - I: 바코드이미지수신")
    code = Column(String(10), nullable=True, comment="결과코드 (코드목록 참조)")
    message = Column(String(50), nullable=True, comment="결과메시지 (코드목록 참조)")
    cancel_code = Column(String(10), nullable=True, comment="취소 결과코드 (코드목록 참조)")
    cancel_message = Column(String(50), nullable=True, comment="취소 결과메시지 (코드목록 참조)")
    pinNo = Column(String(20), nullable=True, comment="쿠폰번호 (gubun  'Y' 입력 표시)")
    orderNo = Column(String(20), nullable=True, comment="주문번호")
    couponImgUrl = Column(String(255), nullable=True)
    detail_yn = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="아래 브랜드명부터 pinStatusNm 까지 데이터 가져왔는지 여부")
    brandNm = Column(String(100), nullable=True, comment="브랜드명")
    cnsmPriceAmt = Column(String(20), nullable=True, comment="정상판매단가")
    correcDtm = Column(String(8), nullable=True, comment="변경일자")
    goodsCd = Column(String(12), nullable=True, comment="상품코드")
    goodsNm = Column(String(100), nullable=True, comment="상품명")
    mmsBrandThumImg = Column(String(300), nullable=True, comment="브랜드 썸네일이미지")
    recverTelNo = Column(String(11), nullable=True, comment="수신자번호")
    sellPriceAmt = Column(String(20), nullable=True, comment="실판매단가")
    sendBasicCd = Column(String(30), nullable=True, comment="기본번호")
    sendRstCd = Column(String(10), nullable=True, comment="거래번호")
    sendRstMsg = Column(String(10), nullable=True, comment="발송상태코드")
    sendStatusCd = Column(String(10), nullable=True, comment="발송상태명")
    senderTelNo = Column(String(11), nullable=True, comment="발신자번호")
    validPrdEndDt = Column(String(14), nullable=True, comment="유효기간만료일")
    pinStatusCd = Column(String(40), nullable=True)
    pinStatusNm = Column(String(40), nullable=True)
    is_point_reduce = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="포인트차감 여부")
    crt_date = Column(DateTime, nullable=True, server_default=text("current_timestamp()"))
    upd_date = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_tr_id', 'tr_id'),
        Index('idx_user_id', 'user_id'),
        Index('idx_goods_code', 'goods_code'),
        Index('idx_crt_date', 'crt_date'),
    )