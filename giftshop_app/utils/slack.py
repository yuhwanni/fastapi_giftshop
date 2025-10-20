import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


async def send_slack(message: str):
    """
    슬랙 메시지 전송
    """
    if not SLACK_WEBHOOK_URL:
        print("⚠️ SLACK_WEBHOOK_URL 설정 안됨")
        return

    payload = {"text": message}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(SLACK_WEBHOOK_URL, json=payload)
            if resp.status_code != 200:
                print(f"⚠️ Slack 전송 실패: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"⚠️ Slack 전송 예외 발생: {e}")
