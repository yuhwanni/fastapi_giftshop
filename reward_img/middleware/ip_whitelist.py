from fastapi import Request, HTTPException
from reward_img.config import settings

async def ip_whitelist_middleware(request: Request, call_next):
    client_ip = request.client.host

    # IPv6 → IPv4 (::ffff:127.0.0.1)
    if client_ip.startswith("::ffff:"):
        client_ip = client_ip.replace("::ffff:", "")

    if client_ip not in settings.allowed_ip_set:
        raise HTTPException(status_code=403, detail="Access denied")

    return await call_next(request)
