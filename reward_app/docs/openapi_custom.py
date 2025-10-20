from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI


def custom_openapi(app: FastAPI):
    """JWT BearerAuth를 Swagger에 표시하고 전역 적용"""
    # 캐시된 스키마가 있으면 삭제 (중요!)
    app.openapi_schema = None

    openapi_schema = get_openapi(
        title="FastAPI Example with JWT & Logging",
        version="1.0.0",
        description="API with JWT Auth, Logging, and Swagger Authorization",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"]["OAuth2PasswordBearer"]["flows"]["password"].update({
        "tokenUrl": "/login",
        "scopes": {},
        "x-tokenName": "Authorization",
        # ✅ Swagger UI 기본값 설정
        "x-default-username": "hong@example.com",
        "x-default-password": "user_password123"
    })
    print('hi')

    app.openapi_schema = openapi_schema
    return app.openapi_schema

    # BearerAuth security scheme 정의
    # openapi_schema["components"]["securitySchemes"] = {
    #     "BearerAuth": {
    #         "type": "http",
    #         "scheme": "bearer",
    #         "bearerFormat": "JWT",
    #         "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'",
    #     }
    # }

    # # ✅ 전역 security 필드 추가 → 이것이 있어야 /docs에 'Authorize' 버튼이 뜹니다.
    # openapi_schema["security"] = [{"BearerAuth": []}]

    # # ✅ login, public 엔드포인트만 security 제외
    # for path in openapi_schema["paths"]:
    #     if path in ["/login", "/public"]:
    #         print(path)
    #         for method in openapi_schema["paths"][path]:
    #             if "security" in openapi_schema["paths"][path][method]:
    #                 del openapi_schema["paths"][path][method]["security"]

    # app.openapi_schema = openapi_schema
    # return app.openapi_schema
