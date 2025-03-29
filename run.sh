#!/bin/bash

# 가상환경 존재 여부 확인
if [ ! -d "venv" ]; then
  echo "가상환경이 없습니다. 먼저 환경 설정을 진행합니다..."
  ./setup.sh
  echo "환경 설정이 완료되었습니다."
fi

# 가상환경 활성화
source venv/bin/activate

# 메인 프로그램 실행
echo "프로그램을 실행합니다..."
python main.py

# 종료 시 가상환경 비활성화
deactivate 