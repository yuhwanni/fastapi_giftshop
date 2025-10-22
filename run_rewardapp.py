import os
import uvicorn

if __name__ == "__main__":
    env = os.getenv("ENV", "development")
    reload = env != "production"
    # log_level = "DEBUG" if reload else "WARNING"

    log_config_path = "reward.app.log.ini"
    
    uvicorn.run(
        "reward_app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=reload,        
        # log_config=log_config_path,
        # log_level=log_level,
        access_log=True,
    )
