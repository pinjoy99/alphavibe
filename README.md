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
  - RSI 전략 (암호화폐 변동성에 최적화된 개선 버전)
- 각 전략별 지표 시각화 (RSI, MACD, Bollinger Bands, SMA)
- 전략 성과 분석 및 시각화
- **실시간 계좌 정보 조회 및 분석**
- **포트폴리오 자산 분포 및 손익 시각화**
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
./run.sh --account                     # 계좌 정보 조회 모드
./run.sh -a                            # 계좌 정보 조회 모드 (단축 옵션)
```

## 환경 변수 설정

이 애플리케이션에서는 민감한 정보만 `.env` 파일에 저장하고, 일반적인 설정값은 모두 `src/utils/config.py` 파일에서 직접 관리합니다.

### 환경 변수 파일 설정 방법

1. `.env.example` 파일을 `.env`로 복사합니다:
   ```
   cp .env.example .env
   ```

2. `.env` 파일을 열어 필요한 민감한 정보를 입력합니다:
   ```
   # Upbit API 키 설정 (필수)
   UPBIT_ACCESS_KEY=your_access_key_here
   UPBIT_SECRET_KEY=your_secret_key_here

   # 텔레그램 설정 (선택사항)
   TELEGRAM_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here
   ```

3. 민감한 정보 설명:

   | 환경 변수 | 설명 |
   |-----------|------|
   | UPBIT_ACCESS_KEY | Upbit API 액세스 키 |
   | UPBIT_SECRET_KEY | Upbit API 시크릿 키 |
   | TELEGRAM_TOKEN | 텔레그램 봇 토큰 |
   | TELEGRAM_CHAT_ID | 텔레그램 채팅 ID |

4. 일반 설정값 변경 방법:

   모든 일반 설정값은 `src/utils/config.py` 파일에서 직접 수정할 수 있습니다. 주요 설정값은 다음과 같습니다:

   | 설정 | 설명 | 기본값 |
   |------|------|--------|
   | CHART_SAVE_PATH | 차트 이미지 저장 경로 | results/analysis |
   | BACKTEST_RESULT_PATH | 백테스트 결과 저장 경로 | results/strategy_results |
   | DEFAULT_INTERVAL | 기본 시간 간격 | day |
   | DEFAULT_COUNT | 조회할 데이터 개수 | 100 |
   | LOG_LEVEL | 로그 레벨 | INFO |
   | ENABLE_TELEGRAM | 텔레그램 알림 활성화 여부 | False |
   | DEFAULT_INITIAL_CAPITAL | 백테스팅 기본 초기 자본 | 1,000,000원 |
   | DEFAULT_BACKTEST_PERIOD | 백테스팅 기본 기간 | 3개월 |
   | COMMISSION_RATE | 거래 수수료율 | 0.05% |
   | SMALL_AMOUNT_THRESHOLD | 소액 코인 기준값 | 500원 |
   | TOP_COIN_COUNT | 상위 코인 표시 개수 | 5개 |

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

4. 계좌 정보 조회:
```
./run.sh --account  # 계좌 정보 조회
./run.sh -a  # 계좌 정보 조회 (단축 옵션)
./run.sh -a -t  # 계좌 정보 조회 및 텔레그램 알림 활성화
```
계좌 정보 조회 기능은 다음 정보를 제공합니다:
- 보유 현금
- 총 자산 가치
- 코인별 보유 현황 (가치 기준 정렬)
- 코인별 손익 정보 (금액 및 백분율)
- 소액 코인 통합 요약
- 최근 주문 내역
- 자산 분포 및 손익 시각화 차트

5. 결과 확인:
   - 콘솔에 각 종목의 기본 통계 정보가 출력됩니다.
   - `results/analysis` 폴더에 분석 차트 이미지가 저장됩니다.
   - `results/strategy_results` 폴더에 백테스트 결과 차트 이미지가 저장됩니다.
   - `results/account` 폴더에 계좌 정보 차트 이미지가 저장됩니다.
   - `results/account_history` 폴더에 계좌 정보 히스토리가 CSV 파일로 저장됩니다.
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
├── results/                  # 결과 데이터 저장 폴더
│   ├── analysis/             # 분석 차트 저장 폴더
│   ├── strategy_results/     # 백테스트 결과 저장 폴더
│   ├── account/              # 계좌 정보 차트 저장 폴더
│   └── account_history/      # 계좌 정보 히스토리 저장 폴더
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
│   ├── trading/              # 거래 관련 모듈
│   │   ├── __init__.py       # 모듈 초기화
│   │   ├── account.py        # 계좌 정보 관리 클래스
│   ├── utils/                # 유틸리티 함수
│   └── visualization/        # 시각화 모듈
│       ├── __init__.py       # 모듈 초기화
│       ├── charts.py         # 차트 생성 함수
│       ├── account_charts.py # 계좌 정보 차트 함수
│       ├── styles.py         # 차트 스타일 설정
│       └── utils.py          # 시각화 유틸리티 함수
└── venv/                     # 가상환경 (Git에서 무시됨)
```

## 모듈 설명

### API 모듈 (src/api)
Upbit API와 통신하여 과거 가격 데이터를 가져오고, 계좌 정보를 조회합니다.

### 백테스팅 모듈 (src/backtest)
다양한 트레이딩 전략을 시뮬레이션하고 결과를 분석합니다.

### 전략 모듈 (src/strategies)
트레이딩 전략 구현. 전략 패턴을 사용하여 모듈화되어 있어 쉽게 새로운 전략을 추가할 수 있습니다.

### 거래 모듈 (src/trading)
계좌 정보 관리 및 분석, 자산 분포 계산 등 거래와 관련된 기능을 제공합니다.

### 알림 모듈 (src/notification)
텔레그램을 통한 분석 결과, 백테스팅 결과, 계좌 정보 알림 기능을 제공합니다.

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
- RSI 전략: 암호화폐 시장의 높은 변동성에 최적화된 RSI 전략
  - 더 좁은 RSI 범위(기본값 35-65)를 사용하여 변동성 높은 시장에서 더 많은 매매 기회 포착
  - 출구 전략 적용: 진입 후 더 작은 RSI 변동(기본값 45-55)에서도 포지션 청산
  - 지수이동평균(EMA)을 사용하여 RSI 계산, 시장 변화에 더 빠르게 반응
  - 매수/매도 포지션 추적으로 효율적인 거래 관리

### 3. 계좌 정보 조회 및 분석
계좌 정보 조회 모드에서는 다음과 같은 정보를 제공합니다:
- 현재 보유 중인 암호화폐의 현황과 통계 정보
- 코인별 평가금액, 매수평균가, 손익 정보
- 소액 코인들을 "기타" 항목으로 묶어서 가독성 향상
- 최근 주문 내역
- 다음 시각화 차트 제공:
  - 자산 분포 파이 차트: 현금 및 각 코인별 비중 시각화
  - 코인별 손익 차트: 코인별 손익 금액 및 손익률 비교
- 계좌 히스토리를 CSV 형식으로 저장하여 추적 가능

### 4. 전략별 차트 시각화
각 전략에 맞는 시각화 제공:
- SMA 전략: 단기 및 장기 이동평균선 표시
- 볼린저 밴드 전략: 상단/중간/하단 밴드 표시
- MACD 전략: MACD, 시그널 라인, 히스토그램 표시
- RSI 전략: RSI 지표와 과매수/과매도 영역 시각화, 진입/퇴출 레벨 표시

### 5. 자동화 백테스팅
소스 코드 변경 시 자동으로 백테스팅을 실행하여 전략 개발과 테스트 과정을 효율화합니다.

## 참고사항

- 기본적으로 BTC(비트코인), ETH(이더리움), XRP(리플)의 데이터를 분석합니다.
- 다른 종목을 분석하려면 `main.py` 파일의 `tickers` 리스트를 수정하세요.
- 업비트에서 제공하는 모든 암호화폐 종목에 대해 분석이 가능합니다.
- 계좌 정보 조회 및 주문 내역 조회를 위해서는 API 키 설정이 필수입니다.
- 차트 스타일과 파라미터는 시각화 모듈에서 쉽게 조정할 수 있습니다.
- 새로운 전략을 추가하려면 `BaseStrategy` 클래스를 상속받아 구현하고 팩토리에 등록하면 됩니다.
- 소액 코인(기본값 500원 미만)은 "기타" 항목으로 묶어서 표시하며, 이 기준값은 수정 가능합니다.