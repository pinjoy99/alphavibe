#!/bin/bash

# 가상환경이 이미 존재하는지 확인
if [ -d "venv" ]; then
  echo "가상환경이 이미 존재합니다."
else
  echo "가상환경을 생성합니다..."
  python -m venv venv
  echo "가상환경 생성 완료!"
fi

# 가상환경 활성화
source venv/bin/activate

# 필요한 패키지 설치
echo "필요한 패키지를 설치합니다..."
pip install -r requirements.txt

# .env 파일이 없으면 .env.example 파일을 복사
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  echo ".env 파일이 없습니다. .env.example 파일을 복사합니다."
  cp .env.example .env
  echo ".env 파일을 생성했습니다. 필요한 설정 값을 수정해주세요."
fi

echo "환경 설정이 완료되었습니다!"
echo "프로그램을 실행하려면 ./run.sh 명령어를 사용하세요."

# 가상환경 비활성화
deactivate 