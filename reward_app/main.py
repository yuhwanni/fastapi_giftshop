from fastapi import FastAPI, Depends
from reward_app.middleware.logging_middleware import (
    LoggingMiddleware,
    simple_logging_middleware,
    SelectiveLoggingMiddleware
)
from reward_app.utils.log_util import app_logger
from reward_app.routes import auth, notice, quote, quiz, referral, attendance, code, login, point, my
from reward_app.docs.openapi_custom import custom_openapi
from contextlib import asynccontextmanager
from reward_app.core.security import get_current_user

from reward_app.database.async_db import async_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('start')

    await async_db._initialize()

    # app.openapi = lambda: custom_openapi(app)
    yield    
    print('end')

app = FastAPI(title="Pincash Reward App API", lifespan=lifespan)

# ✅ 미들웨어 등록
app.middleware("http")(simple_logging_middleware)

@app.get("/health")
async def health():
    is_healthy = await async_db.health_check()
    pool_status = await async_db.get_pool_status()
    return {
        "database": "정상" if is_healthy else "비정상",
        "pool": pool_status
    }

app.include_router(code.router, prefix="/code",tags=["코드"])

app.include_router(login.router, tags=["로그인"])
app.include_router(my.router, prefix="/my",tags=["내 정보"])
# ✅ 라우터 등록
app.include_router(auth.router, prefix="/auth",tags=["회원가입, 아이디/비밀번호찾기"])
# app.include_router(signup.router, prefix="/signup", tags=["SignUp"])
app.include_router(notice.router, prefix="/notice", tags=["공지"], dependencies=[Depends(get_current_user)])

app.include_router(quote.router, prefix="/quote",tags=["명언"], dependencies=[Depends(get_current_user)])
app.include_router(quiz.router, prefix="/quiz",tags=["퀴즈"], dependencies=[Depends(get_current_user)])
app.include_router(referral.router, prefix="/referral",tags=["추천인"], dependencies=[Depends(get_current_user)])

app.include_router(attendance.router, prefix="/attendance",tags=["출석체크"])
app.include_router(point.router, prefix="/point",tags=["포인트"])
# app.include_router(attendance.router, prefix="/attendance",tags=["출석체크"], dependencies=[Depends(get_current_user)])



# ✅ Swagger 전역 인증 적용
# @app.on_event("startup")
# async def set_custom_openapi():
    
    
