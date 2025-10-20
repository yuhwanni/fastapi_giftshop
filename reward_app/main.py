from fastapi import FastAPI, Depends
from reward_app.middleware.logging_middleware import logging_middleware
from reward_app.routes import auth, notice, quote, quiz, referral, attendance, code
from reward_app.docs.openapi_custom import custom_openapi
from contextlib import asynccontextmanager
from reward_app.core.security import get_current_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('start')    
    # app.openapi = lambda: custom_openapi(app)
    yield    
    print('end')

app = FastAPI(title="Pincash Reward App API", lifespan=lifespan)

# ✅ 미들웨어 등록
app.middleware("http")(logging_middleware)

app.include_router(code.router, prefix="/list",tags=["코드"])
# ✅ 라우터 등록
app.include_router(auth.router, prefix="/auth",tags=["로그인, 회원가입, 아이디/비밀번호찾기"])
# app.include_router(signup.router, prefix="/signup", tags=["SignUp"])
app.include_router(notice.router, prefix="/notice", tags=["공지"], dependencies=[Depends(get_current_user)])

app.include_router(quote.router, prefix="/quote",tags=["명언"], dependencies=[Depends(get_current_user)])
app.include_router(quiz.router, prefix="/quiz",tags=["퀴즈"], dependencies=[Depends(get_current_user)])
app.include_router(referral.router, prefix="/referral",tags=["추천인"], dependencies=[Depends(get_current_user)])

# app.include_router(attendance.router, prefix="/attendance",tags=["출석체크"], dependencies=[Depends(get_current_user)])
app.include_router(attendance.router, prefix="/attendance",tags=["출석체크"])


# ✅ Swagger 전역 인증 적용
# @app.on_event("startup")
# async def set_custom_openapi():
    
    
