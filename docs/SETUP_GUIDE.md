# 환경 설정 및 실행 방법

## 환경 설정

환경 설정 스크립트 실행:
```
chmod +x setup.sh
./setup.sh                # 기본 설정 - 가상환경이 없는 경우만 생성
./setup.sh --force        # 가상환경을 강제로 재생성
./setup.sh -f             # 가상환경을 강제로 재생성 (단축 옵션)
./setup.sh --help         # 도움말 표시
```

이 스크립트는 다음 작업을 수행합니다:
- 가상환경(venv) 생성
- 필요한 패키지 설치

또는 수동으로 환경 설정:
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
deactivate
```

## 프로그램 실행

실행 스크립트 사용:
```
chmod +x run.sh
./run.sh                               # 기본 분석 모드
./run.sh --backtest --strategy sma     # SMA 전략으로 백테스팅
./run.sh --backtest --strategy bb      # 볼린저 밴드 전략으로 백테스팅
./run.sh --backtest --strategy macd    # MACD 전략으로 백테스팅
./run.sh --backtest --strategy rsi     # RSI 전략으로 백테스팅
./run.sh --backtest --strategy sma --period 6m --invest 5000000  # 추가 옵션
./run.sh --account                     # 계좌 정보 조회 모드
./run.sh -a                            # 계좌 정보 조회 모드 (단축 옵션)
``` 