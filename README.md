# 암호화폐 가격 분석 및 백테스팅 시스템

이 프로젝트는 암호화폐의 과거 가격 정보를 수집하고 분석하며, 여러 트레이딩 전략을 백테스팅할 수 있는 시스템입니다.

## 기능

- 지정된 암호화폐의 과거 가격 데이터 수집 (Upbit API 사용)
- 기본 통계 정보 계산 (최고가, 최저가, 거래량 등)
- 가격 차트 생성 및 시각화
- 다양한 트레이딩 전략 구현 및 백테스팅:
  - SMA (단순 이동평균) 전략
  - 볼린저 밴드 전략
  - MACD 전략
  - RSI 전략
- 전략 성과 분석 및 시각화
- 텔레그램 알림 지원
- 자동화된 백테스팅 스크립트

## 환경 설정 및 실행 방법

### 환경 설정

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

### 프로그램 실행

실행 스크립트 사용:
```
chmod +x run.sh
./run.sh                               # 기본 분석 모드
./run.sh --backtest --strategy sma     # SMA 전략으로 백테스팅
./run.sh --backtest --strategy bb      # 볼린저 밴드 전략으로 백테스팅
./run.sh --backtest --strategy macd    # MACD 전략으로 백테스팅
./run.sh --backtest --strategy rsi     # RSI 전략으로 백테스팅
./run.sh --backtest --strategy sma --period 6m --invest 5000000  # 추가 옵션
```

### 자동 백테스팅 실행

소스 파일 변경 시 자동으로 백테스트를 실행하는 스크립트:
```
chmod +x watch_and_test.sh
./watch_and_test.sh                    # 기본 설정으로 실행
./watch_and_test.sh --files "src/strategies/*.py main.py"  # 특정 파일만 모니터링
./watch_and_test.sh --command "./run.sh --backtest --strategy macd"  # 다른 백테스트 명령 실행
```

## 환경 변수 설정

프로그램 실행에 필요한 환경 변수는 `.env` 파일에 설정합니다.

### 환경 변수 파일 설정 방법

1. `.env.example` 파일을 `.env`로 복사합니다:
   ```
   cp .env.example .env
   ```

2. `.env` 파일을 열어 필요한 설정 값을 입력합니다:
   ```
   # Upbit API 키 설정 (필수)
   UPBIT_ACCESS_KEY=your_access_key_here
   UPBIT_SECRET_KEY=your_secret_key_here

   # 텔레그램 설정 (선택사항)
   ENABLE_TELEGRAM=false  # 텔레그램 알림을 사용하려면 true로 변경
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here
   ```

3. 환경 변수 설명:

   | 환경 변수 | 설명 | 기본값 |
   |-----------|------|--------|
   | CHART_SAVE_PATH | 차트 이미지 저장 경로 | charts |
   | BACKTEST_RESULT_PATH | 백테스트 결과 저장 경로 | backtest_results |
   | DEFAULT_INTERVAL | 기본 시간 간격 (day, minute1, minute3, minute5 등) | day |
   | DEFAULT_COUNT | 조회할 데이터 개수 | 100 |
   | LOG_LEVEL | 로그 레벨 (INFO, DEBUG, WARNING, ERROR) | INFO |
   | UPBIT_ACCESS_KEY | Upbit API 액세스 키 | - |
   | UPBIT_SECRET_KEY | Upbit API 시크릿 키 | - |
   | ENABLE_TELEGRAM | 텔레그램 알림 활성화 여부 (true/false) | false |
   | TELEGRAM_BOT_TOKEN | 텔레그램 봇 토큰 | - |
   | TELEGRAM_CHAT_ID | 텔레그램 채팅 ID | - |

**참고**: `setup.sh` 스크립트 실행 시 `.env` 파일이 없는 경우 자동으로 `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.

## 사용 방법

1. 환경 설정:
```
./setup.sh
```

2. 기본 실행:
```
./run.sh  # 기본 실행 (가격 분석)
./run.sh --telegram  # 텔레그램 알림 활성화
./run.sh -t  # 텔레그램 알림 활성화 (단축 옵션)
```

3. 백테스팅 실행:
```
./run.sh --backtest --strategy sma  # SMA 전략 백테스팅
./run.sh -b -s bb  # 볼린저 밴드 전략 백테스팅 (단축 옵션)
./run.sh -b -s macd -p 6m -i 5000000  # MACD 전략, 6개월, 5백만원 초기 자본
```

4. 자동 백테스팅 실행:
```
./watch_and_test.sh  # 파일 변경 감지 시 자동 백테스팅
```

5. 결과 확인:
   - 콘솔에 각 종목의 기본 통계 정보가 출력됩니다.
   - `charts` 폴더에 분석 차트 이미지가 저장됩니다.
   - `backtest_results` 폴더에 백테스팅 결과 차트 이미지가 저장됩니다.
   - 텔레그램 알림을 활성화한 경우, 봇을 통해 알림과 차트가 전송됩니다.

## 프로젝트 구조

```
├── .env                      # 환경 변수 설정 파일
├── .env.example              # 환경 변수 예제 파일
├── .gitignore                # Git 무시 파일 목록
├── main.py                   # 메인 프로그램
├── requirements.txt          # 필요 패키지 목록
├── run.sh                    # 실행 스크립트
├── setup.sh                  # 환경 설정 스크립트
├── watch_and_test.sh         # 자동 백테스팅 스크립트
├── charts/                   # 차트 이미지 저장 폴더
├── backtest_results/         # 백테스트 결과 저장 폴더
├── src/                      # 소스 코드
│   ├── api/                  # API 관련 코드
│   ├── backtest/             # 백테스팅 엔진
│   ├── notification/         # 알림 관련 코드 (텔레그램 등)
│   ├── strategies/           # 거래 전략 구현
│   │   ├── __init__.py       # 모듈 초기화
│   │   ├── base_strategy.py  # 기본 전략 인터페이스
│   │   ├── sma_strategy.py   # SMA 전략 구현
│   │   ├── bb_strategy.py    # 볼린저 밴드 전략 구현
│   │   ├── macd_strategy.py  # MACD 전략 구현
│   │   ├── rsi_strategy.py   # RSI 전략 구현
│   │   └── factory.py        # 전략 팩토리
│   ├── utils/                # 유틸리티 함수
│   └── visualization/        # 시각화 모듈
│       ├── __init__.py       # 모듈 초기화
│       ├── charts.py         # 차트 생성 함수
│       ├── styles.py         # 차트 스타일 설정
│       └── utils.py          # 시각화 유틸리티 함수
└── venv/                     # 가상환경 (Git에서 무시됨)
```

## 모듈 설명

### API 모듈 (src/api)
Upbit API와 통신하여 과거 가격 데이터를 가져옵니다.

### 백테스팅 모듈 (src/backtest)
다양한 트레이딩 전략을 시뮬레이션하고 결과를 분석합니다.

### 전략 모듈 (src/strategies)
트레이딩 전략 구현. 전략 패턴을 사용하여 모듈화되어 있어 쉽게 새로운 전략을 추가할 수 있습니다.

### 알림 모듈 (src/notification)
텔레그램을 통한 분석 결과 및 백테스팅 결과 알림 기능을 제공합니다.

### 시각화 모듈 (src/visualization)
차트 생성 및 스타일링을 위한 모듈. 다양한 차트 타입과 스타일을 지원합니다.

## 주요 기능 설명

### 1. 가격 분석
기본 모드에서는 지정된 암호화폐의 가격 데이터를 수집하고 분석하여 기본 통계와 차트를 생성합니다.

### 2. 백테스팅
다양한 트레이딩 전략을 과거 데이터로 시뮬레이션하여 성능을 평가합니다. 지원하는 전략:
- SMA 전략: 단기 이동평균선이 장기 이동평균선을 상향 돌파할 때 매수, 하향 돌파할 때 매도
- 볼린저 밴드 전략: 가격이 하단 밴드에 닿으면 매수, 상단 밴드에 닿으면 매도
- MACD 전략: MACD 선이 시그널 선을 상향 돌파할 때 매수, 하향 돌파할 때 매도
- RSI 전략: RSI가 과매도 수준에서 상승할 때 매수, 과매수 수준에서 하락할 때 매도

### 3. 자동화 백테스팅
소스 코드 변경 시 자동으로 백테스팅을 실행하여 전략 개발과 테스트 과정을 효율화합니다.

## 참고사항

- 기본적으로 BTC(비트코인), ETH(이더리움), XRP(리플)의 데이터를 분석합니다.
- 다른 종목을 분석하려면 `main.py` 파일의 `tickers` 리스트를 수정하세요.
- 업비트에서 제공하는 모든 암호화폐 종목에 대해 분석이 가능합니다.
- API 키는 선택사항이며, 설정하지 않아도 기본적인 시세 조회는 가능합니다.
- 차트 스타일과 파라미터는 시각화 모듈에서 쉽게 조정할 수 있습니다.
- 새로운 전략을 추가하려면 `BaseStrategy` 클래스를 상속받아 구현하고 팩토리에 등록하면 됩니다.