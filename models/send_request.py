from pydantic import BaseModel, Field

class SendRequest(BaseModel):
    goods_code: str = Field(..., min_length=12, max_length=12, description="상품코드")
    mms_msg: str = Field(..., min_length=3, max_length=100, description="MMS 메시지")
    mms_title: str = Field(..., min_length=3, max_length=20, description="MMS 제목")
    phone_no: str = Field(..., min_length=9, max_length=12, description="'-' 제외한 수신번호")
    # user_id: str = Field(..., min_length=3, description="회원 ID")
    
    rev_info_yn: str | None = Field(None, description="예약발송여부 (Y/N)")
    rev_info_date: str | None = Field(None, description="예약일자 (yyyyMMdd)")
    rev_info_time: str | None = Field(None, description="예약시간 (HHmm)")
    template_id: str | None = Field(None, description="카드 아이디")
    banner_id: str | None = Field(None, description="배너 아이디")
    gubun: str | None = Field("N", description="MMS 발송 구분자 (Y:핀번호, N:MMS, I:이미지)")
