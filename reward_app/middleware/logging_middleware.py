import logging
from starlette.types import Message
from starlette.background import BackgroundTask
from fastapi import Request, Response

import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

logger = logging.getLogger("api_logger")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# -----------------------------
# 로그 설정
# -----------------------------
today_str = datetime.now().strftime("%Y%m%d")
log_dir = os.path.join("logs", today_str)
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "database.log")

logger = logging.getLogger("DatabaseLogger")
logger.setLevel(logging.INFO)
file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def end_log_info(res_body: bytes):
    logger.info(f"RESPONSE: {res_body.decode(errors='ignore')}")


def entry_log_info(endpoint: str):
    logger.info(f"ENDPOINT: {endpoint}")


async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {"type": "http.request", "body": body}
    request._receive = receive


async def logging_middleware(request: Request, call_next):
    # req_body = await request.body()
    # await set_body(request, req_body)

    # endpoint = f"{request.method} {request.url.path}?{request.url.query} | {request.client.host} | BODY={req_body.decode(errors='ignore')}"
    # entry_log_info(endpoint)

    # response = await call_next(request)

    # res_body = b""
    # async for chunk in response.body_iterator:
    #     res_body += chunk

    # task = BackgroundTask(end_log_info, res_body)

    # return Response(
    #     content=res_body,
    #     status_code=response.status_code,
    #     headers=dict(response.headers),
    #     media_type=response.media_type,
    #     background=task,
    # )

    req_body = await request.body()
    await set_body(request, req_body)
    endpoint = f"{request.method} {request.url.path} {request.url.query} {req_body} {request.client.host} {request.headers}"

    entry_log_info(endpoint)

    response = await call_next(request)

    res_body = b""
    async for chunk in response.body_iterator:
        res_body += chunk

    # task = BackgroundTask(end_log_info, res_body)

    return Response(
        content=res_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        # background=task,
    )
