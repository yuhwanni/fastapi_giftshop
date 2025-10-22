# reward_app/utils/log_util.py
import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

LOG_BASE_DIR = "rewardapp_logs"


def get_log_dir():
    """날짜별 로그 디렉토리 반환"""
    today = datetime.now().strftime("%Y%m%d")
    log_dir = os.path.join(LOG_BASE_DIR, today)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def setup_logger(name: str, log_filename: str = None, level=logging.INFO):
    """
    로거 설정 함수 (중복 방지, 날짜별 디렉토리)
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 설정되어 있으면 중복 설정 방지
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(level)
    logger.propagate = False  # 상위 로거로 전파 방지
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 파일 핸들러 (날짜별 디렉토리)
    if log_filename is None:
        log_filename = "app.log"
    
    log_dir = get_log_dir()
    log_path = os.path.join(log_dir, log_filename)
    
    file_handler = TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",
        interval=1,
        backupCount=30,  # 30일치 보관
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y%m%d"  # 파일명 suffix 형식
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 앱 전역 로거
app_logger = setup_logger("app_logger", "app.log", level=logging.INFO)
api_logger = setup_logger("api_logger", "api.log", level=logging.INFO)
db_logger = setup_logger("db_logger", "db.log", level=logging.INFO)


# 편의 함수들
def log_info(message: str):
    app_logger.info(message)


def log_error(message: str, exc_info=False):
    app_logger.error(message, exc_info=exc_info)


def log_warning(message: str):
    app_logger.warning(message)


def log_debug(message: str):
    app_logger.debug(message)