#!/bin/bash

# 기본값 설정
FORCE_RECREATE="false"

# 매개변수 처리
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --force|-f)
      FORCE_RECREATE="true"
      shift
      ;;
    --help|-h)
      echo "사용법: ./setup.sh [옵션]"
      echo "옵션:"
      echo "  --force, -f    가상환경이 존재하는 경우에도 강제로 재생성"
      echo "  --help, -h     도움말 표시"
      exit 0
      ;;
    *)
      echo "알 수 없는 옵션: $key"
      echo "도움말을 보려면 ./setup.sh --help 를 실행하세요."
      exit 1
      ;;
  esac
done

# 가상환경 설정
if [ -d "venv" ]; then
  if [ "$FORCE_RECREATE" = "true" ]; then
    echo "기존 가상환경을 삭제하고 새로 생성합니다..."
    rm -rf venv
    python -m venv venv
    echo "가상환경 재생성 완료!"
  else
    echo "가상환경이 이미 존재합니다."
    echo "강제로 재생성하려면 --force 또는 -f 옵션을 사용하세요."
  fi
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