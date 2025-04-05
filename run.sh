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
ACCOUNT="false"

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
    --account|-a)
      ACCOUNT="true"
      shift
      ;;
    --help|-h)
      echo "===== AlphaVibe - 암호화폐 백테스팅 및 분석 도구 ====="
      echo "사용법: ./run.sh [옵션]"
      echo ""
      echo "옵션:"
      echo "  --telegram, -t             텔레그램 알림 활성화"
      echo "  --backtest, -b             백테스팅 모드 활성화"
      echo "  --strategy, -s STRATEGY    백테스팅 전략 선택 (sma, bb, macd, rsi 중 선택, 기본값: sma)"
      echo "  --period, -p PERIOD        백테스팅 기간 (예: 1d, 3d, 1w, 1m, 3m, 6m, 1y, 기본값: 3m)"
      echo "  --invest, -i AMOUNT        백테스팅 초기 투자금액 (기본값: 1,000,000원)"
      echo "  --account, -a              계좌 정보 조회 모드 활성화"
      echo "  --help, -h                 도움말 표시"
      echo ""
      echo "전략 정보:"
      echo "  sma   - 이동평균선 전략: 단기(10일)와 장기(30일) 이동평균선의 교차 시점에 매수/매도 신호 발생"
      echo "          골든 크로스(단기>장기) 시 매수, 데드 크로스(단기<장기) 시 매도"
      echo "  bb    - 볼린저 밴드 전략: 20일 이동평균선을 중심으로 표준편차(2.0)에 따른 밴드를 활용"
      echo "          하단 밴드 터치 시 매수, 상단 밴드 터치 시 매도"
      echo "  macd  - MACD 전략: 단기(12일)와 장기(26일) 지수이동평균의 차이와 신호선(9일)을 활용"
      echo "          MACD선이 신호선을 상향 돌파 시 매수, 하향 돌파 시 매도"
      echo "  rsi   - RSI 전략: 14일 기준 RSI 지표로 과매수(70)/과매도(30) 상태를 활용"
      echo "          과매도 상태에서 반등 시 매수, 과매수 상태에서 하락 시 매도"
      echo ""
      echo "기간 표기법:"
      echo "  1d    - 1일 (day)          1w    - 1주 (week)"
      echo "  1m    - 1개월 (month)      3m    - 3개월 (month)"
      echo "  6m    - 6개월 (month)      1y    - 1년 (year)"
      echo ""
      echo "데이터 조회 정보:"
      echo "  - 6개월 이상(6m, 1y): 일봉 데이터 사용"
      echo "  - 3~6개월(3m): 4시간 데이터 사용"
      echo "  - 1~3개월(1m): 1시간 데이터 사용"
      echo "  - 1개월 미만(1d, 1w): 1시간 데이터 사용"
      echo ""
      echo "예시:"
      echo "  ./run.sh                         기본 분석 모드 실행"
      echo "  ./run.sh -t                      텔레그램 알림 활성화하여 분석 모드 실행"
      echo "  ./run.sh -b                      SMA 전략으로 3개월 백테스팅 실행"
      echo "  ./run.sh -b -s macd -p 6m        MACD 전략으로 6개월 백테스팅 실행"
      echo "  ./run.sh -b -s rsi -p 3m -i 2000000  RSI 전략, 3개월 기간, 초기자본 200만원으로 백테스팅"
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

# 가상환경 활성화 (존재하는 경우에만)
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
  source "$SCRIPT_DIR/venv/bin/activate"
else
  echo "가상환경을 찾을 수 없습니다. 시스템 환경에서 실행합니다."
fi

# 명령줄 옵션 구성
OPTIONS=""

# 텔레그램 알림 상태 출력 및 옵션 추가
if [ "$TELEGRAM" = "true" ]; then
  echo "텔레그램 알림이 활성화되었습니다."
  OPTIONS="$OPTIONS --telegram"
fi

# 계좌 정보 조회 상태 출력 및 옵션 추가
if [ "$ACCOUNT" = "true" ]; then
  echo "계좌 정보 조회 모드가 활성화되었습니다."
  OPTIONS="$OPTIONS --account"
fi

# 백테스팅 상태 출력 및 옵션 추가
if [ "$BACKTEST" = "true" ]; then
  echo "백테스팅 모드가 활성화되었습니다."
  echo "  - 전략: $STRATEGY"
  echo "  - 기간: $PERIOD"
  echo "  - 초기 투자금액: $INVEST"
  
  OPTIONS="$OPTIONS --backtest --strategy $STRATEGY --period $PERIOD --invest $INVEST"
elif [ "$ACCOUNT" = "true" ]; then
  echo "계좌 정보 조회 모드로 실행합니다."
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