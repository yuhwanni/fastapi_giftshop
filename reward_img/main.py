import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from reward_img.config import settings
from reward_img.middleware.ip_whitelist import ip_whitelist_middleware

app = FastAPI()

# IP 화이트리스트 미들웨어
app.middleware("http")(ip_whitelist_middleware)

# StaticFiles 경로 검증
if not os.path.isdir(settings.image_static_path):
    raise RuntimeError(
        f"IMAGE_STATIC_PATH not found: {settings.image_static_path}"
    )

# 이미지 정적 제공
app.mount(
    "/images",
    StaticFiles(directory=settings.image_static_path),
    name="images",
)
