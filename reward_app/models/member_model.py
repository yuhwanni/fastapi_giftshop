from sqlalchemy import Column, String, Integer, DateTime, Enum, text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Member(Base):
    __tablename__ = "PC_MEMBER"

    user_seq = Column(Integer, nullable=False, primary_key=True, autoincrement=True, comment="회원 순번")
    user_email = Column(String(255), nullable=False, comment="ID_사용자 email주소")
    user_sns_key = Column(String(255), nullable=True, comment="SNS고유키")
    user_pwd = Column(String(256), nullable=True, comment="패스워드")
    user_pwd2 = Column(String(256), nullable=True, comment="패스워드임시")
    user_name = Column(String(32), nullable=True, comment="이름")
    nickname = Column(String(32), nullable=True, comment="닉네임")
    user_phone = Column(String(128), nullable=True, comment="전화번호")
    user_gender = Column(Enum('F', 'M'), nullable=True, comment="성별")
    user_birth = Column(String(10), nullable=True, comment="생년월일")
    solar_lunar = Column(Enum('S', 'L'), nullable=True, server_default=text("'S'"), comment="양력,음력")
    time_of_birth = Column(String(5), nullable=True, comment="태어난시각")
    user_location = Column(String(50), nullable=True, comment="위치")
    user_token = Column(String(255), nullable=True, comment="푸쉬토큰")
    device_id = Column(String(255), nullable=True, comment="디바이스 아이디")
    user_point = Column(Integer, nullable=False, server_default=text("0"), comment="회원포인트")
    referral_code = Column(String(10), nullable=False, server_default=text("''"), comment="추천인코드")
    user_stat = Column(Enum('Y', 'N'), nullable=False, server_default=text("'Y'"), comment="상태(Y사용:N중지)")
    user_sns_type = Column(Enum('NS', 'G', 'N', 'K'), nullable=False, server_default=text("'NS'"), comment="일반가입,구글,네이버,카카오")
    user_img = Column(String(255), nullable=True, comment="사용자 프로필 이미지")
    last_login_date = Column(DateTime, nullable=True, comment="마지막 로그인 일자")
    push_status = Column(Enum('Y', 'N'), nullable=True, server_default=text("'N'"), comment="푸시허용")
    push_date = Column(DateTime, nullable=True, comment="푸시등록일-수정일")
    terms_yn = Column(Enum('Y','N'), nullable=False, server_default=text("'Y'"), comment="마케팅 정보 수신 동의")
    privacy_yn = Column(Enum('Y','N'), nullable=False, server_default=text("'Y'"), comment="마케팅 정보 수신 동의")
    marketing_yn = Column(Enum('Y','N'), nullable=False, server_default=text("'Y'"), comment="마케팅 정보 수신 동의")
    crt_date = Column(DateTime, nullable=False, server_default=text("current_timestamp()"), comment="생성일자")
    crt_id = Column(String(20), nullable=True, comment="생성자")
    upd_date = Column(DateTime, nullable=True, onupdate=text("current_timestamp()"), comment="수정일자")
    upd_id = Column(String(20), nullable=True, comment="수정자")
