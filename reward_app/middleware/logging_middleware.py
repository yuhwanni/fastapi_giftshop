import logging
from starlette.types import Message
from starlette.background import BackgroundTask
from fastapi import Request, Response

logger = logging.getLogger("api_logger")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def end_log_info(res_body: bytes):
    logger.info(f"RESPONSE: {res_body.decode(errors='ignore')}")


def entry_log_info(endpoint: str):
    logger.info(f"ENDPOINT: {endpoint}")


async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {"type": "http.request", "body": body}
    request._receive = receive


async def logging_middleware(request: Request, call_next):
    req_body = await request.body()
    await set_body(request, req_body)

    endpoint = f"{request.method} {request.url.path}?{request.url.query} | {request.client.host} | BODY={req_body.decode(errors='ignore')}"
    entry_log_info(endpoint)

    response = await call_next(request)

    res_body = b""
    async for chunk in response.body_iterator:
        res_body += chunk

    task = BackgroundTask(end_log_info, res_body)

    return Response(
        content=res_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
        background=task,
    )
