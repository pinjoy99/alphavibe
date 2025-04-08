# 프로젝트 구조

이 문서는 AlphaVibe 프로젝트의 디렉토리 및 파일 구조를 설명합니다.

## 프로젝트 디렉토리 구조

```
alphavibe/
│
├── main.py                   # 프로그램 진입점
├── run.sh                    # 실행 스크립트
├── requirements.txt          # 필요 패키지 목록
│
├── src/                      # 소스 코드
│   ├── api/                  # API 상호작용
│   ├── analysis/             # 시장 분석
│   ├── indicators/           # 기술적 지표 계산
│   ├── backtest/             # 백테스팅 엔진 (Backtesting.py 기반)
│   ├── strategies/           # 거래 전략 구현
│   ├── trading/              # 실시간 거래 관련
│   ├── utils/                # 유틸리티 함수
│   ├── notification/         # 알림 시스템
│   └── visualization/        # 시각화 도구
│
├── data/                     # 데이터 저장소
│   ├── historical/           # 히스토리컬 데이터
│   └── cache/                # 캐시 데이터
│
├── results/                  # 결과 저장
│   ├── analysis/             # 분석 결과
│   ├── backtest_charts/      # 백테스트 차트
│   ├── account/              # 계좌 정보
│   └── account_history/      # 계좌 내역
│
└── docs/                     # 문서
    ├── USAGE_GUIDE.md        # 사용법 가이드
    ├── ADDING_STRATEGIES.md  # 전략 추가 가이드
    └── PROJECT_STRUCTURE.md  # 이 파일
```

## 주요 모듈 설명

### API 모듈 (`src/api/`)

- **upbit_api.py**: 업비트 API와 상호작용, 가격 데이터 조회 등
- **price_api.py**: 가격 데이터 관련 공통 인터페이스

### 분석 모듈 (`src/analysis/`)

- **market_analyzer.py**: 시장 분석 도구, 기본 통계 계산 등
- **technical_analysis.py**: 기술적 분석 도구
- **pattern_recognition.py**: 차트 패턴 인식

### 지표 모듈 (`src/indicators/`)

- **trend.py**: 추세 지표 (이동평균 등)
- **momentum.py**: 모멘텀 지표 (RSI, MACD 등)
- **volatility.py**: 변동성 지표 (볼린저 밴드 등)
- **volume.py**: 거래량 지표

### 백테스팅 모듈 (`src/backtest/`)

- **backtest_engine_bt.py**: Backtesting.py 기반 백테스팅 엔진
  - 가격 데이터를 입력받아 전략을 실행하고 거래 결과 분석
  - 다양한 성능 지표 계산 (수익률, 최대 낙폭, 샤프 비율 등)
  - 거래 데이터 및 결과 시각화

### 전략 모듈 (`src/strategies/`)

- **strategy_registry.py**: 전략 자동 등록 및 관리 시스템
- **sma_strategy_bt.py**: Backtesting.py 기반 단순 이동평균선 교차 전략

### 거래 모듈 (`src/trading/`)

- **account.py**: 계좌 관리 및 자산 정보 조회
- **order.py**: 주문 처리
- **position.py**: 포지션 관리

### 유틸리티 모듈 (`src/utils/`)

- **config.py**: 설정 관리
- **logger.py**: 로깅 시스템
- **validators.py**: 입력 유효성 검사
- **date_utils.py**: 날짜/시간 관련 유틸리티

### 알림 모듈 (`src/notification/`)

- **telegram.py**: 텔레그램 봇 알림
- **email.py**: 이메일 알림

### 시각화 모듈 (`src/visualization/`)

- **price_charts.py**: 가격 차트 시각화
- **backtest_charts.py**: 백테스트 결과 시각화
- **trading_charts.py**: 거래 관련 시각화
- **indicator_plots.py**: 지표 시각화