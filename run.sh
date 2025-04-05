#!/bin/bash

# 기본값 설정
TELEGRAM="false"

# 매개변수 처리
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --telegram|-t)
      TELEGRAM="true"
      shift
      ;;
    --help|-h)
      echo "사용법: ./run.sh [옵션]"
      echo "옵션:"
      echo "  --telegram, -t    텔레그램 알림 활성화"
      echo "  --help, -h        도움말 표시"
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
if [ ! -d "venv" ]; then
  echo "가상환경이 없습니다. 먼저 환경 설정을 진행합니다..."
  ./setup.sh
  echo "환경 설정이 완료되었습니다."
fi

# 가상환경 활성화
source venv/bin/activate

# 텔레그램 알림 상태 출력
if [ "$TELEGRAM" = "true" ]; then
  echo "텔레그램 알림이 활성화되었습니다."
  # 텔레그램 옵션을 명령줄 인자로 전달
  TELEGRAM_OPTION="--telegram"
else
  echo "텔레그램 알림이 비활성화되었습니다."
  TELEGRAM_OPTION=""
fi

# 메인 프로그램 실행 (명령줄 인자로 전달)
echo "프로그램을 실행합니다..."
python main.py $TELEGRAM_OPTION

# 종료 시 가상환경 비활성화
deactivate 