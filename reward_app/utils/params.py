from enum import Enum

class EarnUseType(str, Enum):
    EARN = "E"  # 적립
    USE = "U"   # 사용

class AgreementYn(str, Enum):
    Y = "Y"  #  동의
    N = "N"   # 미동의

class GenderType(str, Enum):
    F = "F" # 여성
    M = "M" # 남성
    U = "U" # 알수없음음