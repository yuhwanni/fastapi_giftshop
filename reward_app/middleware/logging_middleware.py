# reward_app/middleware/logging_middleware.py
import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from reward_app.utils.log_util import api_logger
import traceback
from reward_app.core.config import make_resp
from fastapi.responses import JSONResponse


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    API 요청/응답 로깅 미들웨어 (메모리 효율적)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 요청 정보 로깅
        await self._log_request(request)
        
        # 요청 처리
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 응답 정보 로깅
            self._log_response(request, response, process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            api_logger.error(
                f"ERROR | {request.method} {request.url.path} | "
                f"{request.client.host} | {process_time:.3f}s | {str(e)}",
                exc_info=True
            )
            raise
    
    async def _log_request(self, request: Request):
        """요청 로깅 (민감한 정보 제외)"""
        try:
            # Body 읽기 (크기 제한)
            body = await request.body()
            body_str = ""
            
            # Body가 너무 크면 일부만 로깅
            if len(body) > 0:
                if len(body) > 1000:  # 1KB 제한
                    body_str = body[:1000].decode(errors='ignore') + "...(truncated)"
                else:
                    body_str = body.decode(errors='ignore')
                
                # JSON이면 파싱 시도
                try:
                    body_json = json.loads(body_str.replace("...(truncated)", ""))
                    # 민감한 필드 마스킹
                    if isinstance(body_json, dict):
                        for sensitive_key in ['password', 'token', 'secret', 'api_key']:
                            if sensitive_key in body_json:
                                body_json[sensitive_key] = "***MASKED***"
                        body_str = json.dumps(body_json, ensure_ascii=False)
                except:
                    pass
            
            # 쿼리 파라미터
            query = str(request.url.query) if request.url.query else ""
            
            log_msg = (
                f"REQUEST | {request.method} {request.url.path} | "
                f"Client: {request.client.host} | "
                f"Query: {query} | "
                f"Body: {body_str if body_str else 'empty'}"
            )
            
            api_logger.info(log_msg)
            
        except Exception as e:
            api_logger.error(f"Request logging error: {e}")
    
    def _log_response(self, request: Request, response: Response, process_time: float):
        """응답 로깅"""
        log_msg = (
            f"RESPONSE | {request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Time: {process_time:.3f}s"
        )
        
        if response.status_code >= 400:
            api_logger.warning(log_msg)
        else:
            api_logger.info(log_msg)


# 기존 함수형 미들웨어 (간단한 버전)
async def simple_logging_middleware(request: Request, call_next):
    """
    간단한 로깅 미들웨어 (Body 로깅 없음)
    """
    start_time = time.time()
    
    # 요청 로깅
    api_logger.info(
        f"→ {request.method} {request.url.path} | "
        f"Client: {request.client.host} | "
        f"Query: {request.url.query or 'none'}"
    )
    
    # 처리
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 응답 로깅
        status_emoji = "✅" if response.status_code < 400 else "❌"
        api_logger.info(
            f"{status_emoji} {request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Time: {process_time:.3f}s"
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        api_logger.error(
            f"❌ {request.method} {request.url.path} | "
            f"Error: {str(e)} | Time: {process_time:.3f}s",
            exc_info=True
        )
        err_msg = traceback.format_exc()
        api_logger.error(err_msg)  
        
        return JSONResponse(
            status_code=500,
            content={
                "code":"E102",                
                "error": str(e),
                "msg": err_msg,
                "path": str(request.url),
            },
        )


# 특정 경로 제외용 미들웨어
class SelectiveLoggingMiddleware(BaseHTTPMiddleware):
    """
    특정 경로는 로깅에서 제외
    """
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 제외 경로는 로깅 없이 통과
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # 나머지는 로깅
        start_time = time.time()
        
        api_logger.info(
            f"→ {request.method} {request.url.path} | {request.client.host}"
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            api_logger.info(
                f"← {response.status_code} | {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            api_logger.error(f"Error: {str(e)}", exc_info=True)
            raise