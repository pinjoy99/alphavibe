# AlphaVibe 아키텍처 문서

## 프로젝트 구조

AlphaVibe는 다음과 같은 주요 모듈로 구성되어 있습니다:

```
alphavibe/
├── main.py                # 메인 진입점
├── run.sh                 # 실행 스크립트
├── setup.sh               # 환경 설정 스크립트
├── src/
│   ├── api/               # API 통신 관련 모듈
│   ├── analysis/          # 시장 분석 모듈
│   ├── backtest/          # 백테스팅 관련 모듈
│   ├── indicators/        # 기술적 지표 계산 모듈
│   ├── notification/      # 알림 관련 모듈
│   ├── strategies/        # 트레이딩 전략 모듈
│   ├── trading/           # 실제 거래 관련 모듈
│   ├── utils/             # 유틸리티 함수
│   └── visualization/     # 시각화 관련 모듈
└── docs/                  # 문서
```

## 모듈 설명

### API 모듈 (src/api)

거래소 API와의 통신을 담당합니다. 주로 Upbit API를 사용합니다.

### 분석 모듈 (src/analysis)

암호화폐 시장 데이터를 분석하여 기술적 지표를 해석하고 시장 상황을 파악합니다.

- **market_analyzer.py**: 시장 분석의 핵심 클래스 제공
- **technical_analysis.py**: 기술적 지표 해석 및 분석
- **pattern_recognition.py**: 차트 패턴 인식 
- **signals.py**: 매매 신호 생성

주요 기능:
1. 시장 데이터 조회 및 처리
2. 기술적 지표 계산 및 해석
3. 지지/저항선 분석
4. 차트 패턴 인식
5. 매매 신호 생성

분석 모듈은 indicators 모듈을 사용하여 기술적 지표를 계산하고, visualization 모듈을 통해 분석 결과를 시각화합니다.

### 백테스팅 모듈 (src/backtest)

트레이딩 전략의 과거 성능을 테스트합니다.

### 지표 모듈 (src/indicators)

다양한 기술적 지표를 계산하는 함수를 제공합니다.

### 알림 모듈 (src/notification)

텔레그램 등을 통한 알림 기능을 제공합니다.

### 전략 모듈 (src/strategies)

다양한 트레이딩 전략을 구현합니다.

### 거래 모듈 (src/trading)

실제 거래 실행 및 계좌 정보 관리를 담당합니다.

### 시각화 모듈 (src/visualization)

차트 및 데이터 시각화를 담당합니다. 모듈화된 구조로 다양한 시각화 기능을 제공합니다:

- **base_charts.py**: 기본 차트 생성 및 공통 요소 관리
- **analysis_charts.py**: 시장 분석 관련 차트 생성
- **indicator_charts.py**: 기술적 지표 시각화
- **backtest_charts.py**: 백테스팅 결과 시각화
- **trading_charts.py**: 계좌 및 거래 관련 시각화
- **styles.py**: 차트 스타일 정의 및 관리
- **viz_helpers.py**: 시각화 내부 헬퍼 함수

주요 기능:
1. 다양한 차트 타입 지원 (캔들스틱, OHLC, 라인 등)
2. 기술적 지표 시각화 (이동평균, MACD, RSI, 볼린저 밴드 등)
3. 백테스팅 결과 시각화 및 성과 비교
4. 자산 분포 및 손익 시각화
5. 다양한 차트 스타일 지원 (기본, 다크모드, 트레이딩뷰 스타일 등)
6. 커스텀 스타일 및 차트 구성 지원

모든 차트는 표준화된 인터페이스를 통해 제공되며, `__init__.py`에서 주요 함수들을 임포트하여 외부 모듈에서 쉽게 사용할 수 있습니다.

```python
# 예시: 시각화 모듈 사용 방법
from src.visualization import plot_price_with_indicators, plot_market_analysis

# 기본 차트 생성
chart_path = plot_price_with_indicators(
    df, 
    "KRW-BTC", 
    ma_windows=[20, 50, 200],
    show_bollinger=True, 
    show_volume=True
)

# 시장 분석 차트 생성
chart_path, analysis_meta = plot_market_analysis(
    df, 
    "KRW-BTC", 
    indicator_config={
        'ma': True,
        'macd': True,
        'rsi': True,
        'support_resistance': True
    }
)
```

## 모듈 간 관계

```
                                  ┌─────────────┐
                                  │   main.py   │
                                  └──────┬──────┘
                                         │
            ┌───────────┬────────────────┼────────────┬───────────┐
            │           │                │            │           │
    ┌───────▼──────┐   ┌▼───────────┐   ┌▼──────────┐ │  ┌───────▼─────┐
    │    api       │   │  analysis   │   │ backtest  │ │  │ notification│
    └───────┬──────┘   └┬───────────┘   └┬──────────┘ │  └─────────────┘
            │           │                │            │
            │      ┌────▼────┐      ┌────▼────┐  ┌────▼────┐
            └──────►indicators◄──────┤strategies│  │  trading│
                   └────┬────┘      └─────┬────┘  └─────────┘
                        │                 │
                        └────────►visualization◄────────┘
```

### 주요 데이터 흐름

1. **분석 흐름**: 
   ```
   API → 데이터 조회 → Analysis → Indicators → Visualization → 결과
   ```

2. **백테스팅 흐름**: 
   ```
   API → 데이터 조회 → Backtest → Strategies → Indicators → Visualization → 결과
   ```

3. **실시간 거래 흐름**: 
   ```
   API → 데이터 조회 → Trading → Strategies → Indicators → API → 주문 실행
   ```

## 분석 모듈 상세 설명

분석 모듈은 단일 진입점 함수 `analyze_market()`을 제공하며, 내부적으로 다음과 같은 단계로 작동합니다:

1. `MarketAnalyzer` 클래스 인스턴스 생성
2. 시장 데이터 조회 (`fetch_data()`)
3. 기술적 지표 계산 (`calculate_indicators()`)
4. 시장 분석 수행 (`analyze()`)
5. 분석 결과 시각화 (`visualize()`)
6. 결과 반환

```python
# 예시: 분석 모듈 사용 방법
from src.analysis import analyze_market

# 비트코인 3개월 일봉 데이터 분석
result = analyze_market("KRW-BTC", period="3m", interval="day")

# 분석 결과 사용
print(f"현재가: {result['stats']['current_price']:,.0f} KRW")
print(f"RSI 분석: {result['technical_indicators']['RSI']}")
``` 