#!/bin/bash

# watch_and_test.sh - 파일 변경 감지 및 자동 백테스팅 실행

echo "파일 변경 감지 후 자동 백테스팅 모드를 시작합니다..."
echo "종료하려면 Ctrl+C를 누르세요."

# 모니터링할 파일 지정 (기본값)
WATCH_FILES="main.py src/api/*.py"

# 백테스팅 옵션 (기본값)
BACKTEST_OPTIONS="-b"

# 체크 간격 (초)
CHECK_INTERVAL=2

# 명령줄 인수 처리
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --files|-f)
      WATCH_FILES="$2"
      shift 2
      ;;
    --options|-o)
      BACKTEST_OPTIONS="$2"
      shift 2
      ;;
    --interval|-i)
      CHECK_INTERVAL="$2"
      shift 2
      ;;
    --help|-h)
      echo "사용법: ./watch_and_test.sh [옵션]"
      echo "옵션:"
      echo "  --files, -f \"FILES\"     모니터링할 파일 패턴 (기본값: \"main.py src/api/*.py\")"
      echo "  --options, -o \"OPTIONS\"  백테스팅 실행 옵션 (기본값: \"-b\")"
      echo "  --interval, -i SECONDS   파일 확인 간격 (초, 기본값: 2)"
      echo "  --help, -h               도움말 표시"
      echo ""
      echo "예시:"
      echo "  ./watch_and_test.sh                             # 기본 설정으로 실행"
      echo "  ./watch_and_test.sh -f \"main.py src/*.py\"      # 특정 파일만 모니터링"
      echo "  ./watch_and_test.sh -o \"-b -s macd -p 6m\"      # MACD 전략, 6개월 기간으로 백테스팅"
      echo "  ./watch_and_test.sh -i 5                       # 5초 간격으로 변경 감지"
      exit 0
      ;;
    *)
      echo "알 수 없는 옵션: $key"
      echo "도움말을 보려면 ./watch_and_test.sh --help 를 실행하세요."
      exit 1
      ;;
  esac
done

echo "모니터링 대상 파일: $WATCH_FILES"
echo "백테스팅 옵션: $BACKTEST_OPTIONS"
echo "파일 확인 간격: ${CHECK_INTERVAL}초"
echo ""

# 초기 체크섬 계산
get_checksum() {
  find $WATCH_FILES -type f -exec md5sum {} \; 2>/dev/null | sort | md5sum | awk '{print $1}'
}

LAST_CHECKSUM=$(get_checksum)
SUCCESS_COUNT=0
FAIL_COUNT=0
TOTAL_RUNS=0
START_TIME=$(date +%s)

# 타임스탬프 출력 함수
timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

# 실행 시간 계산 함수
get_elapsed_time() {
  local elapsed=$(($(date +%s) - START_TIME))
  local hours=$((elapsed / 3600))
  local minutes=$(( (elapsed % 3600) / 60 ))
  local seconds=$((elapsed % 60))
  printf "%02d:%02d:%02d" $hours $minutes $seconds
}

# 통계 출력 함수
print_stats() {
  local success_rate=0
  if [ $TOTAL_RUNS -gt 0 ]; then
    success_rate=$(( (SUCCESS_COUNT * 100) / TOTAL_RUNS ))
  fi
  
  echo "-------------------------------------"
  echo "실행 통계:"
  echo "  실행 시간: $(get_elapsed_time)"
  echo "  성공: $SUCCESS_COUNT / 실패: $FAIL_COUNT / 총 실행: $TOTAL_RUNS"
  echo "  성공률: ${success_rate}%"
  echo "-------------------------------------"
}

echo "최초 백테스팅을 실행합니다..."
echo "$(timestamp)"
echo "-------------------------------------"

# 초기 백테스팅 실행
./run.sh $BACKTEST_OPTIONS
if [ $? -eq 0 ]; then
  ((SUCCESS_COUNT++))
else
  ((FAIL_COUNT++))
fi
((TOTAL_RUNS++))

print_stats
echo "변경사항 감지 중... (${CHECK_INTERVAL}초마다 확인)"

trap 'echo -e "\n스크립트를 종료합니다..."; print_stats; exit 0' INT

while true; do
  # 새 체크섬 계산
  CURRENT_CHECKSUM=$(get_checksum)
  
  # 변경사항 있는지 확인
  if [ "$CURRENT_CHECKSUM" != "$LAST_CHECKSUM" ]; then
    echo -e "\n변경사항이 감지되었습니다. 백테스팅을 실행합니다..."
    echo "$(timestamp)"
    echo "-------------------------------------"
    
    # 백테스팅 실행
    ./run.sh $BACKTEST_OPTIONS
    if [ $? -eq 0 ]; then
      ((SUCCESS_COUNT++))
    else
      ((FAIL_COUNT++))
    fi
    ((TOTAL_RUNS++))
    
    # 체크섬 업데이트
    LAST_CHECKSUM=$CURRENT_CHECKSUM
    
    print_stats
    echo "다음 변경사항을 감지하는 중..."
  fi
  
  # 설정된 간격으로 대기
  sleep $CHECK_INTERVAL
done 