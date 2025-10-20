import ipaddress
from fastapi import Request, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from giftshop_app.database.db_core import get_async_session

async def verify_ext_access(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    ext_code = request.headers.get("X-EXT-CODE")
    if not ext_code:
        raise HTTPException(status_code=401, detail="Missing X-EXT-CODE header")

    # 실제 클라이언트 IP 가져오기 (프록시 고려)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host

    # DB에서 ext_code 확인
    query = "SELECT ext_ip FROM API_CALL_EXT WHERE ext_code = :ext_code"
    result = await db.execute(text(query), {"ext_code": ext_code})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=403, detail="Invalid ext_code")

    allowed_ip_list = row[0].split(",")  # 여러 개 허용 가능
    client_ip_obj = ipaddress.ip_address(client_ip)

    def ip_allowed(client_ip_obj, allowed_ip):
        allowed_ip = allowed_ip.strip()
        try:
            if "/" in allowed_ip:  # CIDR
                return client_ip_obj in ipaddress.ip_network(allowed_ip, strict=False)
            else:  # 단일 IP
                return client_ip_obj == ipaddress.ip_address(allowed_ip)
        except ValueError:
            return False

    if not any(ip_allowed(client_ip_obj, ip) for ip in allowed_ip_list):
        raise HTTPException(status_code=403, detail=f"IP not allowed: {client_ip}")

    return True
