# 프로젝트 구조 및 모듈 설명

## 전체 디렉토리 구조

```
├── .env                      # 환경 변수 설정 파일
├── .env.example              # 환경 변수 예제 파일
├── .gitignore                # Git 무시 파일 목록
├── main.py                   # 메인 프로그램
├── requirements.txt          # 필요 패키지 목록
├── run.sh                    # 실행 스크립트
├── setup.sh                  # 환경 설정 스크립트
├── docs/                     # 문서 폴더
│   ├── ADDING_STRATEGIES.md  # 전략 추가 가이드
│   ├── SETUP_GUIDE.md        # 설정 가이드 
│   ├── USAGE_GUIDE.md        # 사용법 가이드
│   ├── PROJECT_STRUCTURE.md  # 프로젝트 구조 문서
│   ├── FEATURES.md           # 기능 설명 문서
│   ├── ENVIRONMENT_VARIABLES.md # 환경 변수 설명
│   └── architecture.md       # 아키텍처 문서
├── results/                  # 결과 데이터 저장 폴더
│   ├── analysis/             # 분석 차트 저장 폴더
│   ├── strategy_results/     # 백테스트 결과 저장 폴더
│   ├── account/              # 계좌 정보 차트 저장 폴더
│   └── account_history/      # 계좌 정보 히스토리 저장 폴더
├── src/                      # 소스 코드
│   ├── api/                  # API 관련 코드
│   ├── analysis/             # 시장 분석 관련 코드
│   ├── backtest/             # 백테스팅 엔진
│   ├── indicators/           # 기술적 지표 계산 모듈
│   ├── notification/         # 알림 관련 코드 (텔레그램 등)
│   ├── strategies/           # 거래 전략 구현
│   │   ├── __init__.py       # 모듈 초기화
│   │   ├── base_strategy.py  # 기본 전략 인터페이스
│   │   ├── sma_strategy.py   # SMA 전략 구현
│   │   ├── bb_strategy.py    # 볼린저 밴드 전략 구현
│   │   ├── macd_strategy.py  # MACD 전략 구현
│   │   ├── rsi_strategy.py   # RSI 전략 구현
│   │   ├── doomsday_cross_strategy.py # 둠스데이 크로스 전략
│   │   ├── strategy_registry.py # 전략 레지스트리
│   │   ├── template_strategy.py # 전략 템플릿
│   │   └── factory.py        # 전략 팩토리
│   ├── trading/              # 거래 관련 모듈
│   │   ├── __init__.py       # 모듈 초기화
│   │   ├── account.py        # 계좌 정보 관리 클래스
│   ├── utils/                # 유틸리티 함수
│   │   ├── __init__.py       # 모듈 초기화
│   │   ├── config.py         # 중앙화된 설정 관리
│   │   ├── date_utils.py     # 날짜/시간 관련 유틸리티
│   │   ├── validation.py     # 데이터 검증 유틸리티
│   │   ├── file_utils.py     # 파일 관련 유틸리티
│   │   └── chart_utils.py    # 차트 공통 유틸리티 함수
│   └── visualization/        # 시각화 모듈
│       ├── __init__.py       # 모듈 초기화 및 외부 API 정의
│       ├── charts.py         # [DEPRECATED] 이전 차트 함수 (경고 표시)
│       ├── base_charts.py    # 기본 차트 함수
│       ├── analysis_charts.py # 분석 차트 함수 
│       ├── indicator_charts.py # 지표 차트 함수
│       ├── backtest_charts.py # 백테스트 차트 함수
│       ├── trading_charts.py # 트레이딩 및 계좌 차트 함수
│       ├── styles.py         # 차트 스타일 설정
│       └── viz_helpers.py    # 시각화 내부 헬퍼 함수
└── venv/                     # 가상환경 (Git에서 무시됨)
```

## 주요 모듈 설명

### API 모듈 (src/api)
Upbit API와 통신하여 과거 가격 데이터를 가져오고, 계좌 정보를 조회합니다.

### 분석 모듈 (src/analysis)
시장 데이터 분석 및 통계 계산을 수행합니다. 시장 추세, 패턴 인식 및 기본 통계 지표를 계산합니다.

### 지표 모듈 (src/indicators)
다양한 기술적 지표를 계산하는 함수를 제공합니다. RSI, MACD, 볼린저 밴드 등 기술적 지표 계산 로직이 포함되어 있습니다.

### 백테스팅 모듈 (src/backtest)
다양한 트레이딩 전략을 시뮬레이션하고 결과를 분석합니다. 수익률, 최대 낙폭, 거래 횟수 등 다양한 지표를 계산합니다.

### 전략 모듈 (src/strategies)
트레이딩 전략 구현. 전략 패턴을 사용하여 모듈화되어 있어 쉽게 새로운 전략을 추가할 수 있습니다.
- `base_strategy.py`: 모든 전략의 기본 인터페이스
- `strategy_registry.py`: 전략 자동 등록 및 관리 시스템
- `template_strategy.py`: 새 전략 개발을 위한 템플릿
- 각 전략 구현 파일: 구체적인 전략 로직 구현

### 거래 모듈 (src/trading)
계좌 정보 관리 및 분석, 자산 분포 계산 등 거래와 관련된 기능을 제공합니다.

### 유틸리티 모듈 (src/utils)
시스템에서 사용하는 다양한 유틸리티 기능들을 제공합니다.
- `config.py`: 중앙화된 설정 관리 (기본 코인 목록, 기간, 데이터 간격 등)
- `date_utils.py`: 날짜 및 시간 관련 유틸리티 함수
- `validation.py`: 데이터 유효성 검증 함수
- `file_utils.py`: 파일 및 디렉토리 관련 유틸리티 함수

### 알림 모듈 (src/notification)
텔레그램을 통한 분석 결과, 백테스팅 결과, 계좌 정보 알림 기능을 제공합니다.

### 시각화 모듈 (src/visualization)
차트 생성 및 스타일링을 위한 모듈. 다양한 차트 타입과 스타일을 지원합니다. 모듈화된 구조로 재사용성과 가독성이 향상되었습니다.

- `__init__.py`: 모듈 초기화 및 외부 API 정의, 다른 모듈에서 쉽게 사용할 수 있는 인터페이스 제공
- `charts.py`: [DEPRECATED] 이전 차트 생성 함수들 (경고와 함께 새 함수로 리디렉션)
- `base_charts.py`: 기본 가격 차트 및 공통 차트 요소 생성 함수
  - 캔들스틱, OHLC, 라인 차트 그리기
  - 이동평균선, 볼린저 밴드 추가
  - 거래 신호 마커와 주석 추가
- `analysis_charts.py`: 시장 분석 차트 생성 함수
  - 기술적 분석 차트
  - 지표 시각화
  - 지지/저항선 분석
- `indicator_charts.py`: 기술 지표 차트 생성 함수
  - MACD, RSI, 스토캐스틱, ATR, CCI 등 지표 차트
  - 여러 지표를 조합한 차트 생성
- `backtest_charts.py`: 백테스팅 결과 시각화 함수
  - 전략 백테스팅 결과 차트
  - 전략 성과 요약 차트
  - 여러 전략 비교 차트
- `trading_charts.py`: 거래 및 계좌 정보 시각화 함수
  - 자산 분포 파이 차트
  - 코인별 손익 차트
  - 거래 내역 시각화
  - 포트폴리오 가치 변화 추적
- `styles.py`: 차트 스타일 정의 및 적용 함수
  - 기본 스타일, 다크 모드, 트레이딩뷰 스타일 등 지원
  - 커스텀 스타일 생성 기능
- `viz_helpers.py`: 시각화 모듈 내부에서 사용하는 헬퍼 함수

차트 관련 공통 유틸리티 함수들은 `src/utils/chart_utils.py`로 이동했습니다. 