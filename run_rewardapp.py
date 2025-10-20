import uvicorn

if __name__ == "__main__":    
    uvicorn.run("reward_app.main:app", host="0.0.0.0", port=8002, reload=True)
