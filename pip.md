pip install fastapi uvicorn[standard] sqlalchemy aiomysql dotenv asyncio python-dotenv httpx typing-inspect apscheduler python-jose[cryptography] bcrypt email-validator

aiomysql



# 포트 변경
uvicorn main:app --host 0.0.0.0 --port 8001
# 시작? 재시작?
uvicorn main:app --reload


nohup uvicorn main:app --host 0.0.0.0 --port 8001 &

nohup /usr/local/bin/python3.11 -m uvicorn main:app --host 0.0.0.0 --port 8001 > nohup.out 2>&1 &

nohup /usr/local/bin/python3.11 /usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 8001

nohup /usr/local/bin/python3.11 /home/git_project_2025/fastapi_giftshop/run_giftshop.py > /home/git_project_2025/giftshop_app.out 2>&1 &
nohup /usr/local/bin/python3.11 /home/git_project_2025/fastapi_giftshop/run_rewardapp.py > /home/git_project_2025/reward_app.out 2>&1 &

# 기프티쇼에서 브랜드와 상품 가져오기
python ./batch/fetch_brand_goods_batch.py
# 기프티쇼에서 상품 보낸 후 쿠폰정보(상품정보) 불러오기
python ./batch/fetch_send_goods_batch.py

fastapi 실행시 스케줄러로 동작
브랜드 가져오기 1800초에 한번
jobBrands
상품 가져오기 1800초에 한번
jobGoods
쿠폰 데이터 가져오기 10초에 한번
jobSends

.env에 시간 설정
JOB_BRANDS_SEC=1800
JOB_GOODS_SEC=1800
JOB_SENDS_SEC=10