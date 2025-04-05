#!/bin/bash

# 스크립트 경로에서 절대 경로 구하기
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 기본값 설정
TELEGRAM="false"
BACKTEST="false"
STRATEGY="sma"
PERIOD="3m"
INVEST="1000000"

# 매개변수 처리
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --telegram|-t)
      TELEGRAM="true"
      shift
      ;;
    --backtest|-b)
      BACKTEST="true"
      shift
      ;;
    --strategy|-s)
      STRATEGY="$2"
      shift 2
      ;;
    --period|-p)
      PERIOD="$2"
      shift 2
      ;;
    --invest|-i)
      INVEST="$2"
      shift 2
      ;;
    --help|-h)
      echo "사용법: ./run.sh [옵션]"
      echo "옵션:"
      echo "  --telegram, -t             텔레그램 알림 활성화"
      echo "  --backtest, -b             백테스팅 모드 활성화"
      echo "  --strategy, -s STRATEGY    백테스팅 전략 선택 (sma, bb, macd 중 선택, 기본값: sma)"
      echo "  --period, -p PERIOD        백테스팅 기간 (예: 1d, 3d, 1w, 1m, 3m, 6m, 1y, 기본값: 3m)"
      echo "  --invest, -i AMOUNT        백테스팅 초기 투자금액 (기본값: 1000000)"
      echo "  --help, -h                 도움말 표시"
      echo ""
      echo "예시:"
      echo "  ./run.sh                    기본 분석 모드 실행"
      echo "  ./run.sh -t                 텔레그램 알림 활성화하여 분석 모드 실행"
      echo "  ./run.sh -b                 SMA 전략으로 3개월 백테스팅 실행"
      echo "  ./run.sh -b -s macd -p 6m   MACD 전략으로 6개월 백테스팅 실행"
      exit 0
      ;;
    *)
      echo "알 수 없는 옵션: $key"
      echo "도움말을 보려면 ./run.sh --help 를 실행하세요."
      exit 1
      ;;
  esac
done

# 가상환경 존재 여부 확인
if [ ! -d "$SCRIPT_DIR/venv" ]; then
  echo "가상환경이 없습니다. 먼저 환경 설정을 진행합니다..."
  "$SCRIPT_DIR/setup.sh"
  echo "환경 설정이 완료되었습니다."
fi

# 가상환경 활성화
source "$SCRIPT_DIR/venv/bin/activate"

# 명령줄 옵션 구성
OPTIONS=""

# 텔레그램 알림 상태 출력 및 옵션 추가
if [ "$TELEGRAM" = "true" ]; then
  echo "텔레그램 알림이 활성화되었습니다."
  OPTIONS="$OPTIONS --telegram"
fi

# 백테스팅 상태 출력 및 옵션 추가
if [ "$BACKTEST" = "true" ]; then
  echo "백테스팅 모드가 활성화되었습니다."
  echo "  - 전략: $STRATEGY"
  echo "  - 기간: $PERIOD"
  echo "  - 초기 투자금액: $INVEST"
  
  OPTIONS="$OPTIONS --backtest --strategy $STRATEGY --period $PERIOD --invest $INVEST"
else
  echo "분석 모드로 실행합니다."
fi

# 메인 프로그램 실행 (명령줄 인자로 전달)
echo "프로그램을 실행합니다..."
python "$SCRIPT_DIR/main.py" $OPTIONS

# 종료 시 가상환경 비활성화 (가상환경이 활성화되어 있으면 비활성화)
if [ -n "$VIRTUAL_ENV" ]; then
  deactivate
fi 