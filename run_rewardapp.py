import os
import uvicorn
import logging.config
import configparser

def load_ini_to_dict(path: str) -> dict:
    """
    INI 파일을 읽어서 dict로 변환 (uvicorn에서 사용 가능)
    """
    config = configparser.ConfigParser()
    config.read(path, encoding="utf-8")  # Windows 한글 문제 방지
    
    # log_dict = {
    #     "version": 1,
    #     "disable_existing_loggers": False,
    #     "formatters": {},
    #     "handlers": {},
    #     "loggers": {},
    # }

    # # formatters
    # for f in config["formatters"]["keys"].split(","):
    #     f = f.strip()
    #     fmt_key = f"formatter_{f}"
    #     fmt = config.get(fmt_key, "format", fallback="%(levelname)s: %(message)s")
    #     log_dict["formatters"][f] = {"format": fmt}

    # # handlers
    # for h in config["handlers"]["keys"].split(","):
    #     h = h.strip()
    #     handler_key = f"handler_{h}"
    #     cls = config.get(handler_key, "class")
    #     level = config.get(handler_key, "level", fallback="INFO")
    #     formatter = config.get(handler_key, "formatter", fallback=None)
    #     args = config.get(handler_key, "args", fallback=None)
    #     log_dict["handlers"][h] = {
    #         "class": cls,
    #         "level": level,
    #         "formatter": formatter,
    #         "args": eval(args) if args else (),
    #     }

    # # loggers
    # for l in config["loggers"]["keys"].split(","):
    #     l = l.strip()
    #     section = f"logger_{l}"
    #     handlers = config.get(section, "handlers", fallback="").replace(" ", "").split(",")
    #     level = config.get(section, "level", fallback="INFO")
    #     log_dict["loggers"][l] = {"handlers": handlers, "level": level}

    # return log_dict

if __name__ == "__main__":
    env = os.getenv("ENV", "development")
    reload = env != "production"
    log_level = "DEBUG" if reload else "WARNING"

    # log_config_path = "reward.app.log.ini"
    # config = configparser.ConfigParser()
    # config.read(log_config_path, encoding="utf-8")  # Windows 한글 문제 방지
    # log_config_dict = load_ini_to_dict(log_config_path)

    # fmt 수정 가능
    # if "formatters" in log_config_dict:
    #     if "default" in log_config_dict["formatters"]:
    #         log_config_dict["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    #     if "access" in log_config_dict["formatters"]:
    #         log_config_dict["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    # print(log_config_dict)
    # print('hi1')
    # print(config['loggers']['Keys'])
    # print('hi2')
    uvicorn.run(
        "reward_app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=reload,        
        # log_config=log_config_path,
        # log_level=log_level,
        access_log=True,
    )
