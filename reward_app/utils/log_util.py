# reward_app/utils/log_util.py
import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


LOG_BASE_DIR = "rewardapp_logs"


class DateCheckingHandler(logging.Handler):
    """로그 작성 시마다 날짜를 체크하는 핸들러"""
    
    def __init__(self, base_dir, filename, level=logging.INFO):
        super().__init__(level)
        self.base_dir = base_dir
        self.log_filename = filename
        self.current_date = None
        self.file_handler = None
        self._update_handler()
    
    def _update_handler(self):
        """날짜가 변경되면 핸들러 업데이트"""
        new_date = datetime.now().strftime("%Y%m%d")
        
        if new_date != self.current_date:
            # 기존 핸들러 닫기
            if self.file_handler:
                self.file_handler.close()
            
            # 새 디렉토리 생성
            self.current_date = new_date
            log_dir = os.path.join(self.base_dir, self.current_date)
            os.makedirs(log_dir, exist_ok=True)
            
            # 새 파일 핸들러 생성
            log_path = os.path.join(log_dir, self.log_filename)
            self.file_handler = TimedRotatingFileHandler(
                filename=log_path,
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8",
            )
            self.file_handler.setFormatter(self.formatter)
    
    def emit(self, record):
        """로그 레코드 작성"""
        self._update_handler()
        self.file_handler.emit(record)


def setup_logger(name: str, log_filename: str = None, level=logging.INFO):
    """
    로거 설정 함수 (날짜별 디렉토리 자동 변경)
    """
    logger = logging.getLogger(name)
    
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(level)
    logger.propagate = False
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 파일 핸들러 (날짜별 디렉토리 자동 변경)
    if log_filename is None:
        log_filename = "app.log"
    
    file_handler = DateCheckingHandler(
        base_dir=LOG_BASE_DIR,
        filename=log_filename,
        level=level
    )
    file_handler.setFormatter(formatter)
    
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


def log_info(message: str):
    app_logger.info(message)


def log_error(message: str, exc_info=False):
    app_logger.error(message, exc_info=exc_info)


def log_warning(message: str):
    app_logger.warning(message)


def log_debug(message: str):
    app_logger.debug(message)