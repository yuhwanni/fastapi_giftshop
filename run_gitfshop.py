import uvicorn

if __name__ == "__main__":
    uvicorn.run("giftshop_app.main:app", host="0.0.0.0", port=8001, reload=True)
