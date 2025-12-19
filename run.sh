#!/bin/bash

# === 설정 ===
PROJECT_DIR="/home/git_project_2025/fastapi_giftshop"
PYTHON_BIN="/usr/local/bin/python3.11"
GIFTSHOP_LOG="/home/git_project_2025/giftshop_app.out"
REWARDAPP_LOG="/home/git_project_2025/reward_app.out"
REWARDIMG_LOG="/home/git_project_2025/reward_img.out"
PORTS=("8001" "8002","8003")

echo "==========================================="
echo "?? FastAPI Giftshop 배포 시작"
echo "==========================================="

# === 1. 프로젝트 디렉토리 이동 ===
cd "$PROJECT_DIR" || { echo "? 디렉토리 이동 실패: $PROJECT_DIR"; exit 1; }

# === 2. 최신 코드 가져오기 ===
echo "?? 최신 코드 가져오는 중..."
git pull
echo "? git pull 완료"
echo "-------------------------------------------"

# === 3. 기존 프로세스 종료 ===
for PORT in "${PORTS[@]}"; do
    echo "?? 포트 $PORT 사용 중인 프로세스 확인 중..."
    PID=$(lsof -ti tcp:$PORT)

    if [ -n "$PID" ]; then
        echo "?? 포트 $PORT 사용 중인 PID: $PID → 종료 중..."
        kill -9 $PID
        echo "? 포트 $PORT 프로세스 종료 완료"
    else
        echo "?? 포트 $PORT 사용 중인 프로세스 없음"
    fi
    echo "-------------------------------------------"
done

\cp -f .env.prod .env

# === 4. 새 프로세스 실행 (nohup.out 방지) ===
echo "?? Giftshop 앱 실행 중..."
nohup "$PYTHON_BIN" "$PROJECT_DIR/run_giftshop.py" > "$GIFTSHOP_LOG" 2>&1 < /dev/null &

echo "?? Rewardapp 앱 실행 중..."
nohup "$PYTHON_BIN" "$PROJECT_DIR/run_rewardapp.py" > "$REWARDAPP_LOG" 2>&1 < /dev/null &

echo "?? Rewardimg 앱 실행 중..."
nohup "$PYTHON_BIN" "$PROJECT_DIR/run_rewardimg.py" > "$REWARDIMG_LOG" 2>&1 < /dev/null &

# === 5. 실행 안정화 대기 ===
echo "? 앱이 포트를 열 때까지 잠시 대기 중...(5초)"
sleep 5

# === 6. 포트 사용 확인 ===
echo "-------------------------------------------"
echo "?? 실행 후 포트 상태 확인"
for PORT in "${PORTS[@]}"; do
    if lsof -i tcp:$PORT | grep LISTEN >/dev/null; then
        echo "? 포트 $PORT 정상적으로 LISTEN 중"
    else
        echo "? 포트 $PORT가 열려있지 않습니다. (앱 실행 실패 가능)"
    fi
done
echo "-------------------------------------------"

echo "==========================================="
echo "? 배포 완료!"
echo "로그 파일:"
echo " - Giftshop: $GIFTSHOP_LOG"
echo " - RewardApp: $REWARDAPP_LOG"
echo " - RewardImg: $REWARDIMG_LOG"
echo "==========================================="
