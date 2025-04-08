# 전략 추가 가이드

AlphaVibe 시스템에 새로운 거래 전략을 추가하는 방법을 설명합니다.

## 1. Backtesting.py 전략 추가하기

### 1.1 전략 파일 생성

Backtesting.py 기반 전략을 구현하기 위해 새 파일을 생성합니다. 파일 이름은 `전략명_bt.py` 형식을 사용하는 것이 좋습니다:

```bash
# 예: RSI 전략 파일 생성
touch src/strategies/rsi_strategy_bt.py
```

### 1.2 전략 클래스 구현

새 파일에 다음 템플릿을 사용하여 전략 클래스를 구현합니다:

```python
from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np

class YourStrategyNameBT(Strategy):
    """
    YourStrategyName 전략 설명
    
    이 전략은 ...
    """
    
    # 전략 메타데이터 (필수)
    CODE = 'your_strategy_code'  # 전략 코드 (명령줄 인자로 사용)
    NAME = '당신의 전략 이름'     # 전략 이름 (표시용)
    DESCRIPTION = '당신의 전략에 대한 설명...'
    
    # 전략 파라미터 
    param1 = 10  # 첫 번째 파라미터
    param2 = 20  # 두 번째 파라미터
    
    def init(self):
        """
        전략 초기화 - 지표 계산
        """
        # 데이터 준비
        price = self.data.Close
        
        # 지표 계산 - I() 함수를 사용하여 등록
        self.indicator1 = self.I(lambda: 계산_로직)
        self.indicator2 = self.I(lambda: 계산_로직)
        
        # 로그 출력
        print(f"전략 초기화: 데이터 수={len(price)}개, 파라미터={self.param1}, {self.param2}")
    
    def next(self):
        """
        매 봉마다 실행되는 트레이딩 로직
        """
        # 매수 조건
        if 매수_조건:
            # 포지션이 없으면 매수
            if not self.position:
                self.buy()
        
        # 매도 조건
        elif 매도_조건:
            # 포지션이 있으면 매도
            if self.position:
                self.sell()
            
    @classmethod
    def get_parameters(cls):
        """
        전략에 사용되는 파라미터와 설명을 반환합니다.
        """
        return {
            'param1': {
                'default': 10,
                'description': '첫 번째 파라미터 설명',
                'type': 'int',
                'min': 2,
                'max': 50
            },
            'param2': {
                'default': 20, 
                'description': '두 번째 파라미터 설명',
                'type': 'int',
                'min': 5,
                'max': 100
            }
        }
```

### 1.3 Backtesting.py 전략 구조 이해하기

Backtesting.py 전략은 두 개의 핵심 메서드로 구성됩니다:

1. **init()**: 전략이 처음 시작될 때 호출되며, 지표를 계산하고 초기화합니다.
   - `self.I()` 메서드를 사용하여 지표를 등록합니다.
   - 람다 함수를 사용하여 계산 로직을 정의합니다.

2. **next()**: 매 봉마다 호출되며, 실제 트레이딩 로직을 구현합니다.
   - `self.buy()`, `self.sell()` 메서드로 거래를 실행합니다.
   - `crossover()` 같은 Backtesting.py 라이브러리 함수를 활용할 수 있습니다.

### 1.4 중요 속성 및 메서드

Backtesting.py 전략에서 사용할 수 있는 주요 속성과 메서드들:

1. **데이터 접근**:
   - `self.data.Close`: 종가 데이터
   - `self.data.Open`: 시가 데이터
   - `self.data.High`: 고가 데이터
   - `self.data.Low`: 저가 데이터
   - `self.data.Volume`: 거래량 데이터
   - `self.data.index`: 날짜/시간 인덱스

2. **거래 메서드**:
   - `self.buy()`: 매수 주문 실행
   - `self.sell()`: 매도 주문 실행
   - `self.position`: 현재 포지션 정보
   - `self.position.close()`: 포지션 종료

3. **지표 계산**:
   - `self.I(lambda: ...)`: 지표 계산 및 등록
   - 지표 값은 시계열로 저장되어 `indicator[-1]`로 접근 가능

## 2. 실제 예제: SMA 전략

다음은 간단한 이동평균 교차 전략의 실제 구현 예시입니다:

```python
# src/strategies/sma_strategy_bt.py
from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd

class SMAStrategyBT(Strategy):
    """
    SMA(Simple Moving Average) 전략 - Backtesting.py 버전
    
    단기 이동평균(short_sma)과 장기 이동평균(long_sma)의 교차를 이용한 전략입니다.
    - 골든 크로스(단기 > 장기): 매수 신호
    - 데드 크로스(단기 < 장기): 매도 신호
    """
    
    # 전략 메타데이터
    CODE = 'sma'
    NAME = '단순 이동평균 교차 전략'
    DESCRIPTION = '단기/장기 이동평균의 교차를 이용한 추세 추종 전략'
    
    # 전략 파라미터
    short_window = 10  # 단기 이동평균 기간
    long_window = 30   # 장기 이동평균 기간
    
    def init(self):
        """
        지표 초기화: 단기 및 장기 이동평균 계산
        """
        # 가격 데이터
        price = self.data.Close
        
        # 이동평균 계산
        self.short_sma = self.I(lambda: pd.Series(price).rolling(self.short_window).mean())
        self.long_sma = self.I(lambda: pd.Series(price).rolling(self.long_window).mean())
    
    def next(self):
        """
        매 봉마다 실행되는 트레이딩 로직
        """
        # 포지션이 없고 골든 크로스 발생 시 매수
        if not self.position and crossover(self.short_sma, self.long_sma):
            self.buy()
        
        # 포지션이 있고 데드 크로스 발생 시 매도
        elif self.position and crossover(self.long_sma, self.short_sma):
            self.sell()
    
    @classmethod
    def get_parameters(cls):
        """
        전략 파라미터 정의
        """
        return {
            'short_window': {
                'default': 10,
                'description': '단기 이동평균 기간',
                'type': 'int',
                'min': 2,
                'max': 50
            },
            'long_window': {
                'default': 30, 
                'description': '장기 이동평균 기간',
                'type': 'int',
                'min': 5,
                'max': 200
            }
        }
```

## 3. 또 다른 예제: RSI 전략

다음은 RSI 지표를 이용한 전략 예시입니다:

```python
# src/strategies/rsi_strategy_bt.py
from backtesting import Strategy
import pandas as pd
import numpy as np

class RSIStrategyBT(Strategy):
    """
    RSI(Relative Strength Index) 전략 - Backtesting.py 버전
    
    RSI 과매수/과매도 지점을 이용한 반전 매매 전략입니다.
    - RSI < oversold: 매수 신호 (과매도 상태에서 매수)
    - RSI > overbought: 매도 신호 (과매수 상태에서 매도)
    """
    
    # 전략 메타데이터
    CODE = 'rsi'
    NAME = 'RSI 과매수/과매도 전략'
    DESCRIPTION = 'RSI 지표의 과매수/과매도 구간을 활용한 반전매매 전략'
    
    # 전략 파라미터
    rsi_period = 14  # RSI 계산 기간
    oversold = 30    # 과매도 기준점
    overbought = 70  # 과매수 기준점
    
    def init(self):
        """
        지표 초기화: RSI 계산
        """
        # 가격 데이터
        price = self.data.Close
        
        # RSI 계산 함수
        def calc_rsi(prices, period=14):
            # 가격 변화 계산
            deltas = pd.Series(prices).diff()
            
            # 상승폭과 하락폭 분리
            gain = deltas.copy()
            loss = deltas.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            loss = -loss
            
            # 평균 계산 (첫 번째 값은 단순 평균)
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # RS 계산
            rs = avg_gain / avg_loss
            
            # RSI 계산
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
        
        # RSI 등록
        self.rsi = self.I(lambda: calc_rsi(price, self.rsi_period))
    
    def next(self):
        """
        매 봉마다 실행되는 트레이딩 로직
        """
        # 현재 RSI 값
        current_rsi = self.rsi[-1]
        
        # 과매도 상태에서 매수
        if current_rsi < self.oversold and not self.position:
            self.buy()
        
        # 과매수 상태에서 매도
        elif current_rsi > self.overbought and self.position:
            self.sell()
    
    @classmethod
    def get_parameters(cls):
        """
        전략 파라미터 정의
        """
        return {
            'rsi_period': {
                'default': 14,
                'description': 'RSI 계산 기간',
                'type': 'int',
                'min': 2,
                'max': 50
            },
            'oversold': {
                'default': 30,
                'description': '과매도 기준점',
                'type': 'int',
                'min': 10,
                'max': 40
            },
            'overbought': {
                'default': 70,
                'description': '과매수 기준점',
                'type': 'int',
                'min': 60,
                'max': 90
            }
        }
```

## 4. 전략 레지스트리에 등록

새 전략은 자동으로 레지스트리에 등록됩니다. 시스템은 `src/strategies` 폴더의 모든 `*_bt.py` 파일을 검색하여 Backtesting.py 기반 전략 클래스를 자동으로 발견하고 등록합니다.

전략이 올바르게 등록되려면 다음 조건을 만족해야 합니다:

1. `backtesting.Strategy` 클래스를 상속
2. 필수 메타데이터 속성 정의: `CODE`, `NAME`, `DESCRIPTION`
3. `init()` 및 `next()` 메서드 구현
4. (선택) `get_parameters()` 클래스 메서드 구현

## 5. 전략 사용 방법

구현한 전략은 다음과 같이 사용할 수 있습니다:

```bash
# RSI 전략 사용 예시
./run.sh -b -s rsi -p 6m -c BTC -i 100000000

# 파라미터 수정
./run.sh -b -s rsi -p 6m -c BTC -i 100000000 --params rsi_period=7,oversold=20,overbought=80
```

## 6. 파라미터 관리

전략 파라미터는 다음 위치에서 설정할 수 있습니다:

1. **기본값**: `get_parameters()` 메서드에서 정의된 기본값
2. **명령줄 인자**: `--params` 플래그를 사용하여 실행 시 지정
   ```bash
   ./run.sh -b -s rsi -p 6m -c BTC --params rsi_period=7,oversold=20
   ```

## 7. 고급 전략 기능

### 7.1 거래량 기반 필터링

거래량에 따라 거래를 필터링하는 예시:

```python
def next(self):
    # 거래량이 평균보다 높은 경우에만 거래
    avg_volume = pd.Series(self.data.Volume).rolling(20).mean()[-1]
    current_volume = self.data.Volume[-1]
    
    if current_volume < avg_volume:
        return  # 거래량이 충분하지 않으면 아무 것도 하지 않음
    
    # 여기에 거래 로직 구현
```

### 7.2 위험 관리

손절매 및 이익실현 구현 예시:

```python
def next(self):
    # 매수 조건
    if 매수_조건 and not self.position:
        entry_price = self.data.Close[-1]
        stop_loss = entry_price * 0.95  # 5% 손절매
        take_profit = entry_price * 1.15  # 15% 이익실현
        
        # 매수 위치 저장
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        
        self.buy()
    
    # 손절매/이익실현 체크
    elif self.position:
        current_price = self.data.Close[-1]
        
        # 손절매
        if current_price <= self.stop_loss:
            self.position.close()
            print(f"손절매 실행: {current_price}")
        
        # 이익실현
        elif current_price >= self.take_profit:
            self.position.close()
            print(f"이익실현 실행: {current_price}")
```

### 7.3 포지션 크기 조정

리스크에 따른 포지션 크기 조정 예시:

```python
def next(self):
    # 매수 조건
    if 매수_조건 and not self.position:
        # 현재 변동성 계산 (ATR 등)
        volatility = 계산된_변동성
        
        # 변동성에 따른 포지션 크기 조정
        size = 1.0 / volatility if volatility > 0 else 1.0
        size = min(1.0, max(0.2, size))  # 20%~100% 범위로 제한
        
        self.buy(size=size)  # 조정된 크기로 매수
```

## 8. 결론

Backtesting.py 기반 전략 개발은 직관적이고 효율적인 방법으로 거래 전략을 구현하고 테스트할 수 있게 해줍니다. 이 가이드를 통해 다양한 전략을 구현하고 실험해보세요.

전략 개발 시 다음 사항을 고려하세요:

1. 충분한 테스트 기간과 데이터를 사용하세요 (최소 6개월 이상 권장).
2. 과최적화를 주의하세요. 너무 많은 파라미터나 복잡한 조건은 과거 데이터에만 최적화될 수 있습니다.
3. 현실적인 거래 비용(수수료)을 고려하세요.
4. 위험 관리를 항상 전략에 포함하세요.