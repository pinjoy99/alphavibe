# 전략 추가 가이드

AlphaVibe 시스템에 새로운 거래 전략을 추가하는 방법을 설명합니다. 두 가지 유형의 전략을 추가할 수 있습니다:

1. **기본 전략**: 자체 개발 백테스팅 엔진용(`BaseStrategy` 상속)
2. **Backtesting.py 전략**: Backtesting.py 라이브러리용(`Strategy` 상속)

## 1. 기본 전략 추가하기 (자체 백테스팅 엔진용)

### 1.1 전략 템플릿 복사 및 수정

1. `src/strategies/template_strategy.py` 파일을 복사하여 새 파일을 만듭니다.
   ```bash
   cp src/strategies/template_strategy.py src/strategies/your_strategy_name.py
   ```

2. 새 파일에서 클래스 이름과 메타데이터를 수정합니다.
   ```python
   class YourStrategyName(BaseStrategy):
       """
       YourStrategyName 전략 클래스
       
       이 전략은 ...
       """
       
       # 전략 메타데이터
       CODE = 'your_strategy_code'  # 전략 코드 (명령줄 인자로 사용)
       NAME = '당신의 전략 이름'     # 전략 이름 (표시용)
       DESCRIPTION = '당신의 전략에 대한 설명...'
   ```

### 1.2 전략 로직 구현

전략의 핵심 로직은 `apply()` 메서드에 구현합니다. 이 메서드는 가격 데이터를 받아 기술적 지표를 계산하고 매수/매도 신호를 생성합니다.

```python
def apply(self, df, params=None):
    """
    전략 로직을 적용하여 매수/매도 신호를 생성합니다.
    
    Args:
        df (pd.DataFrame): 가격 데이터
        params (dict, optional): 전략 파라미터
        
    Returns:
        pd.DataFrame: 신호가 추가된 데이터프레임
    """
    # 파라미터 설정
    short_window = params.get('short_window', 10)
    long_window = params.get('long_window', 30)
    
    # 지표 계산 
    df['short_ma'] = df['close'].rolling(window=short_window).mean()
    df['long_ma'] = df['close'].rolling(window=long_window).mean()
    
    # 시그널 생성
    df['signal'] = 0  # 기본값 = 중립
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1  # 매수 신호
    df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1  # 매도 신호
    
    # 기타 로직...
    
    return df
```

### 1.3 파라미터 정의

전략에 사용되는 파라미터를 정의하고 기본값을 설정합니다.

```python
@classmethod
def get_parameters(cls):
    """
    전략에 사용되는 파라미터와 기본값을 반환합니다.
    
    Returns:
        dict: 파라미터 이름과 기본값
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

## 2. Backtesting.py 전략 추가하기

### 2.1 전략 파일 생성

Backtesting.py 기반 전략은 다른 구조를 가집니다. 새 파일을 만들고 다음 템플릿을 사용하세요:

```python
from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np

class YourStrategyNameBT(Strategy):
    """
    YourStrategyName 전략 - Backtesting.py 버전
    
    이 전략은 ...
    """
    
    # 전략 메타데이터
    CODE = 'your_strategy_code'  # 전략 코드 (명령줄 인자로 사용)
    NAME = '당신의 전략 이름'     # 전략 이름 (표시용)
    DESCRIPTION = '당신의 전략에 대한 설명...'
    
    # 전략 파라미터 
    short_window = 10  # 단기 이동평균 기간
    long_window = 30   # 장기 이동평균 기간
    
    def init(self):
        """
        전략 초기화 - 지표 계산
        """
        # 데이터 준비
        price = self.data.Close
        
        # 지표 계산
        self.short_ma = self.I(lambda: pd.Series(price).rolling(self.short_window).mean())
        self.long_ma = self.I(lambda: pd.Series(price).rolling(self.long_window).mean())
    
    def next(self):
        """
        매 봉마다 실행되는 트레이딩 로직
        """
        # 매수 조건 - 골든 크로스
        if crossover(self.short_ma, self.long_ma):
            self.buy()
        
        # 매도 조건 - 데드 크로스
        elif crossover(self.long_ma, self.short_ma):
            self.sell()
            
    @classmethod
    def get_parameters(cls):
        """
        전략에 사용되는 파라미터와 설명을 반환합니다.
        
        Returns:
            dict: 파라미터 이름과 속성
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

### 2.2 Backtesting.py 전략 구조 이해하기

Backtesting.py 전략은 두 개의 핵심 메서드로 구성됩니다:

1. **init()**: 전략이 처음 시작될 때 호출되며, 지표를 계산하고 초기화합니다.
   - `self.I()` 메서드를 사용하여 지표를 등록합니다.
   - 람다 함수를 사용하여 계산 로직을 정의합니다.

2. **next()**: 매 봉마다 호출되며, 실제 트레이딩 로직을 구현합니다.
   - `self.buy()`, `self.sell()` 메서드로 거래를 실행합니다.
   - `crossover()` 같은 Backtesting.py 라이브러리 함수를 활용할 수 있습니다.

### 2.3 실제 예제: SMA 전략

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

## 3. 전략 레지스트리에 등록

새 전략은 자동으로 레지스트리에 등록됩니다. 시스템은 `src/strategies` 폴더의 모든 전략 클래스를 자동으로 검색하여 등록합니다.

하지만 아래와 같은 경우에는 특별한 처리가 필요할 수 있습니다:

1. 동일한 CODE를 가진 전략이 여러 개 있는 경우(예: 기본 버전과 Backtesting.py 버전)
2. 특정 조건에서만 활성화되어야 하는 전략

이런 경우에는 `src/strategies/__init__.py` 파일을 수정해야 할 수 있습니다.

## 4. 전략 사용 방법

### 4.1 기본 전략 사용

```bash
./run.sh -b -s your_strategy_code -p 6m -c BTC
```

### 4.2 Backtesting.py 전략 사용

```bash
./run.sh -b -s your_strategy_code -bt -p 6m -c BTC
```

여기서 `-bt` 플래그는 Backtesting.py 엔진을 사용하도록 지정합니다.

## 5. 전략 발견 방식

AlphaVibe 시스템은 다음 방식으로 전략을 발견합니다:

1. `src/strategies` 폴더에서 모든 Python 파일을 검색합니다.
2. 각 파일에서 `BaseStrategy` 또는 Backtesting.py의 `Strategy`를 상속받는 클래스를 찾습니다.
3. 발견된 클래스가 필수 속성(`CODE`, `NAME`, `DESCRIPTION`)을 가지고 있는지 확인합니다.
4. 유효한 전략 클래스는 전략 레지스트리에 등록됩니다.

## 6. 파라미터 관리

전략 파라미터는 다음 위치에서 설정할 수 있습니다:

1. **기본값**: `get_parameters()` 메서드에서 정의된 기본값
2. **명령줄 인자**: `--params` 플래그를 사용하여 실행 시 지정
   ```bash
   ./run.sh -b -s your_strategy_code -p 6m -c BTC --params short_window=15,long_window=45
   ```
3. **구성 파일**: `config.py`에 있는 전략별 기본 구성 사용

## 7. 추가 예제: 모멘텀 전략

다음은 간단한 모멘텀 전략 구현 예시입니다:

```python
# src/strategies/momentum_strategy.py
from src.strategies.base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class MomentumStrategy(BaseStrategy):
    """
    모멘텀 전략
    
    이전 기간의 가격 변화를 기반으로 모멘텀을 계산하고, 이를 기반으로 매수/매도 결정
    """
    
    # 전략 메타데이터
    CODE = 'momentum'
    NAME = '모멘텀 전략'
    DESCRIPTION = '가격 모멘텀을 기반으로 하는 트레이딩 전략'
    
    def apply(self, df, params=None):
        """모멘텀 전략 로직 적용"""
        # 파라미터 설정
        window = params.get('window', 14)
        threshold = params.get('threshold', 0)
        
        # 모멘텀 계산 (현재 가격 - n일 전 가격)
        df['momentum'] = df['close'] - df['close'].shift(window)
        
        # 신호 생성
        df['signal'] = 0
        df.loc[df['momentum'] > threshold, 'signal'] = 1  # 매수 신호
        df.loc[df['momentum'] < -threshold, 'signal'] = -1  # 매도 신호
        
        return df
    
    @classmethod
    def get_parameters(cls):
        """전략 파라미터 정의"""
        return {
            'window': {
                'default': 14,
                'description': '모멘텀 계산 기간',
                'type': 'int',
                'min': 1,
                'max': 100
            },
            'threshold': {
                'default': 0,
                'description': '신호 발생 임계값',
                'type': 'float',
                'min': 0,
                'max': 10000
            }
        }
```

## 8. Backtesting.py 모멘텀 전략 예제

다음은 동일한 모멘텀 전략을 Backtesting.py로 구현한 예시입니다:

```python
# src/strategies/momentum_strategy_bt.py
from backtesting import Strategy
import pandas as pd
import numpy as np

class MomentumStrategyBT(Strategy):
    """
    모멘텀 전략 - Backtesting.py 버전
    
    이전 기간의 가격 변화를 기반으로 모멘텀을 계산하고, 이를 기반으로 매수/매도 결정
    """
    
    # 전략 메타데이터
    CODE = 'momentum'
    NAME = '모멘텀 전략'
    DESCRIPTION = '가격 모멘텀을 기반으로 하는 트레이딩 전략'
    
    # 전략 파라미터
    window = 14       # 모멘텀 계산 기간
    threshold = 0     # 신호 발생 임계값
    
    def init(self):
        """지표 초기화"""
        # 가격 데이터
        close = self.data.Close
        
        # 모멘텀 계산 (현재 가격 - n일 전 가격)
        self.momentum = self.I(lambda: pd.Series(close) - pd.Series(close).shift(self.window))
    
    def next(self):
        """트레이딩 로직"""
        # 매수 조건: 모멘텀이 임계값보다 높음
        if self.momentum[-1] > self.threshold and not self.position:
            self.buy()
        
        # 매도 조건: 모멘텀이 음수 임계값보다 낮음
        elif self.momentum[-1] < -self.threshold and self.position:
            self.sell()
    
    @classmethod
    def get_parameters(cls):
        """전략 파라미터 정의"""
        return {
            'window': {
                'default': 14,
                'description': '모멘텀 계산 기간',
                'type': 'int',
                'min': 1,
                'max': 100
            },
            'threshold': {
                'default': 0,
                'description': '신호 발생 임계값',
                'type': 'float',
                'min': 0,
                'max': 10000
            }
        }
```

## 9. 결론

AlphaVibe 시스템에서 전략을 추가하는 방법은 매우 유연합니다. 자체 개발한 백테스팅 엔진과 Backtesting.py 라이브러리 모두를 지원하므로, 사용자의 필요에 맞게 선택할 수 있습니다. 성능과 복잡성을 고려하여 적절한 방식을 선택하세요.

- **자체 백테스팅 엔진**: 복잡한 멀티에셋 포트폴리오 전략에 적합
- **Backtesting.py**: 빠른 개발과 강력한 시각화 도구가 필요한 경우에 적합