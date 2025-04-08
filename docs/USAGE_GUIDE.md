# 사용 방법

## 기본 사용법

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

3. 코인 선택 및 데이터 간격 옵션:
```
./run.sh --coins BTC,SOL  # BTC와 SOL만 분석
./run.sh -c BTC,ETH,DOGE  # 여러 코인 지정 (단축 옵션)
./run.sh --interval minute15  # 15분봉 데이터로 분석 (차트 및 데이터)
./run.sh -v minute60  # 1시간봉 데이터로 분석 (단축 옵션)
./run.sh -c BTC -v minute15 -p 1m  # BTC를 15분봉으로 1개월 데이터 분석
```

데이터 간격 옵션(-v 또는 --interval)을 사용하면 해당 간격으로 데이터를 조회하고 차트를 생성합니다. 지원되는 간격은 다음과 같습니다:
- day: 일봉 데이터
- minute1, minute3, minute5: 1분, 3분, 5분봉
- minute15, minute30: 15분, 30분봉
- minute60, minute240: 1시간, 4시간봉

## 백테스팅 활용

1. 사용 가능한 전략 확인:
```
./run.sh --help
```
이 명령을 실행하면 현재 시스템에서 사용 가능한 모든 전략이 자동으로 표시됩니다. 새로운 전략을 추가하면 별도의 설정 없이 이 목록에 자동으로 표시됩니다.

2. 백테스팅 실행:
```
./run.sh --backtest --strategy sma  # SMA 전략 백테스팅
./run.sh -b -s sma  # SMA 전략 백테스팅 (단축 옵션)
./run.sh -b -s sma -p 6m -i 5000000  # SMA 전략, 6개월, 5백만원 초기 자본
./run.sh -b -c SOL -s sma  # SOL 코인에 대해 SMA 전략으로 백테스팅
./run.sh -b -c BTC,ETH -v minute240  # BTC, ETH에 대해 4시간봉 데이터로 백테스팅
```

### Backtesting.py 기반 백테스팅

AlphaVibe는 Backtesting.py 라이브러리를 사용하여 높은 성능과 정확한 백테스팅 결과를 제공합니다.

```
# SMA 전략으로 BTC 백테스팅 (3개월, 1억원 초기자본)
./run.sh -b -s sma -p 3m -c BTC -i 100000000
```

#### Backtesting.py 엔진의 주요 특징

- **벡터화된 백테스팅**: 행 단위 이터레이션 대신 벡터화된 계산으로 백테스팅 속도가 크게 향상됩니다.
- **고급 성능 지표**: 샤프 비율, 칼마 비율, 최대 낙폭, 승률, 손익비 등 다양한 성능 지표를 자동으로 계산합니다.
- **시각화 도구**: 포지션, 이익/손실, 거래 실행, 드로우다운 등을 포함한 인터랙티브 차트를 제공합니다.
- **포지션 관리**: 다양한 포지션 크기 지정 방법과 포지션 관리 기능을 제공합니다.
- **최적화 도구**: 전략 파라미터 최적화를 위한 도구를 제공합니다.

#### 예시: SMA 전략 백테스팅

```
# 기본 SMA 전략 백테스팅 (10일/30일 이동평균선)
./run.sh -b -s sma -p 3m -c BTC -i 100000000

# SMA 전략 백테스팅 (파라미터 수정)
./run.sh -b -s sma -p 6m -c BTC -i 100000000 --params short_window=20,long_window=50

# 여러 코인에 SMA 전략 적용
./run.sh -b -s sma -p 3m -c BTC,ETH,SOL -i 100000000

# 다른 시간 간격으로 백테스팅
./run.sh -b -s sma -p 6m -c BTC -v minute60 -i 100000000
```

#### 실제 거래 크기를 고려한 백테스팅

고가의 코인(예: BTC)에 대해 백테스팅할 경우 초기 자본이 충분해야 합니다. BTC의 경우 아래와 같이 충분한 초기 자본을 설정하는 것이 좋습니다:

```
# BTC 백테스팅을 위한 충분한 초기 자본 설정
./run.sh -b -s sma -p 3m -c BTC -i 100000000
```

#### 백테스팅 결과 해석

백테스팅 실행 후 출력되는 주요 성능 지표들:

- **총 수익률(%)**: 전략 실행 후 얻은 총 수익률
- **연간 수익률(%)**: 연간으로 환산한 수익률
- **거래 횟수**: 전체 거래 횟수
- **승률(%)**: 이익이 발생한 거래의 비율
- **손익비(Profit Factor)**: 총 이익 / 총 손실
- **최대 낙폭(%)**: 포트폴리오 가치의 최대 하락 폭
- **샤프 비율**: 위험 대비 수익률을 나타내는 지표 (높을수록 좋음)

#### 차트 결과 이해하기

Backtesting.py는 다음과 같은 다양한 차트를 생성합니다:

1. **메인 가격 차트**:
   - 가격 데이터와 이동평균선 표시
   - 매수/매도 포인트 표시
   - 포지션 규모 시각화

2. **지표 차트**:
   - 거래량
   - RSI, MACD 등의 기술적 지표

3. **자산 가치 변화 차트**:
   - 초기 자본 대비 포트폴리오 가치 변화
   - 현금 및 보유 자산 비율 변화

4. **드로우다운 차트**:
   - 포트폴리오 가치의 최대 낙폭을 시각화
   - 위험 관리에 중요한 정보 제공

결과 차트는 `results/backtest_charts` 폴더에 저장됩니다.

#### 파라미터 최적화

특정 전략의 파라미터를 최적화하려면 명령줄에서 직접 다양한 파라미터 조합을 테스트할 수 있습니다:

```
# SMA 단기 이동평균 기간을 5, 10, 15로 테스트
./run.sh -b -s sma -p 6m -c BTC -i 100000000 --params short_window=5
./run.sh -b -s sma -p 6m -c BTC -i 100000000 --params short_window=10
./run.sh -b -s sma -p 6m -c BTC -i 100000000 --params short_window=15

# 단기 및 장기 이동평균 조합 테스트
./run.sh -b -s sma -p 6m -c BTC -i 100000000 --params short_window=10,long_window=30
./run.sh -b -s sma -p 6m -c BTC -i 100000000 --params short_window=20,long_window=50
```

**주의사항**:
- 백테스팅은 일반적으로 최소 7일 이상의 데이터가 필요합니다.
- 짧은 기간을 사용할 경우 최소한 장기 이동평균(기본 30일) 계산에 필요한 데이터 이상을 제공해야 합니다.
- 고가의 코인을 백테스팅할 때는 초기 자본이 충분해야 정확한 결과를 얻을 수 있습니다.

3. 데이터 부족 경고:

각 전략은 정상 작동을 위해 특정 개수 이상의 데이터 행이 필요합니다. 데이터가 부족한 경우(예: 단기간 백테스팅) 시스템은 다음과 같은 친화적인 경고 메시지를 표시합니다:

```
⚠️ 경고: 전략 적용에 최소 35개 행이 필요합니다. 현재: 31
다음 옵션을 시도해보세요:
  1. 더 긴 기간 사용: -p 3m 또는 -p 6m
  2. 더 짧은 시간 간격 사용: -v minute60 또는 -v minute30
  3. 더 많은 데이터가 필요한 전략이므로 다른 전략을 시도
```

이런 경고가 표시되면 다음 해결 방법을 시도해 보세요:
- 더 긴 기간의 데이터 사용: `-p 3m` 또는 `-p 6m`
- 더 작은 시간 간격 사용: `-v minute60` 또는 `-v minute30`
- 필요한 데이터가 더 적은 다른 전략 선택

## 계좌 정보 조회

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

## 결과 확인

- 콘솔에 각 종목의 기본 통계 정보가 출력됩니다.
- `results/analysis` 폴더에 분석 차트 이미지가 저장됩니다.
- `results/backtest_charts` 폴더에 백테스트 결과 차트 이미지가 저장됩니다.
- `results/account` 폴더에 계좌 정보 차트 이미지가 저장됩니다.
- `results/account_history` 폴더에 계좌 정보 히스토리가 CSV 파일로 저장됩니다.
- 텔레그램 알림을 활성화한 경우, 봇을 통해 알림과 차트가 전송됩니다.

## 시각화 결과 예시

시스템은 다양한 시각화 결과를 제공합니다:

1. 백테스트 종합 차트
   - 가격 차트와 이동평균선
   - 매매 시그널 표시 (매수/매도 포인트)
   - 거래량 차트
   - RSI 지표 차트
   - 포트폴리오 가치 변화 차트
   - 드로우다운 차트

## 차트 스타일 변경

차트 스타일을 변경하여 시각화 결과를 커스터마이징할 수 있습니다:

```
./run.sh --style dark  # 다크 모드 스타일로 차트 생성
./run.sh -b -s sma --style tradingview  # 트레이딩뷰 스타일로 백테스트 차트 생성
./run.sh -a --style dark  # 다크 모드로 계좌 정보 차트 생성
```

지원 스타일:
- `default`: 기본 스타일 (밝은 배경, 기본 색상)
- `dark`: 다크 모드 (어두운 배경, 밝은 색상)
- `tradingview`: 트레이딩뷰 스타일 (전문 거래 플랫폼과 유사한 디자인)

## 시각화 모듈 직접 활용

프로젝트 내에서 시각화 모듈을 직접 활용하여 차트를 생성할 수 있습니다:

```python
# 기본 차트 생성
from src.visualization import plot_price_with_indicators

chart_path = plot_price_with_indicators(
    df,                     # OHLCV 데이터
    "KRW-BTC",              # 티커 심볼
    chart_type="candlestick", # 차트 타입 (candlestick, ohlc, line)
    show_volume=True,       # 거래량 표시
    ma_windows=[20, 50, 200], # 이동평균선 기간
    show_bollinger=True,    # 볼린저 밴드 표시
    style="dark"            # 차트 스타일
)

# 백테스트 결과 시각화
from src.visualization import plot_backtest_results

chart_path = plot_backtest_results(
    price_data,             # 가격 데이터
    trade_history,          # 거래 내역
    "SMA",                  # 전략 이름
    "KRW-BTC",              # 티커 심볼
    initial_capital=1000000, # 초기 자본금
    style="tradingview"     # 차트 스타일
)

# 자산 분포 차트
from src.visualization import plot_asset_distribution

chart_path = plot_asset_distribution(
    account_summary,        # 계좌 요약 정보
    style="dark"            # 차트 스타일
) 