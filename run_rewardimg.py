import os
import uvicorn

if __name__ == "__main__":
    env = os.getenv("ENV", "development")
    reload = env != "production"
    # log_level = "DEBUG" if reload else "WARNING"

    
    uvicorn.run(
        "reward_img.main:app",
        host="0.0.0.0",
        port=8003,
        reload=reload,                
        access_log=True,
        proxy_headers=True
    )

