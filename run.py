import asyncio
import uvicorn

async def main():
    config1 = uvicorn.Config("giftshop_app.main:app", host="0.0.0.0", port=8001)
    config2 = uvicorn.Config("reward_app.main:app", host="0.0.0.0", port=8002)

    server1 = uvicorn.Server(config1)
    server2 = uvicorn.Server(config2)

    await asyncio.gather(
        server1.serve(),
        server2.serve()
    )

if __name__ == "__main__":
    asyncio.run(main())
