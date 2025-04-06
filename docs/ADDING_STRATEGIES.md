# 새 거래 전략 추가 방법

이 가이드는 AlphaVibe 시스템에 새로운 거래 전략을 추가하는 방법을 설명합니다.

## 1. 템플릿 파일 복사 및 수정

1. `src/strategies/template_strategy.py` 파일을 복사하여 새 전략 파일 생성:
   ```bash
   cp src/strategies/template_strategy.py src/strategies/your_strategy_name_strategy.py
   ```

2. 새 파일에서 다음 항목을 수정:
   - 클래스 이름 (`TemplateStrategy` → `YourStrategyNameStrategy`)
   - 메타데이터: `STRATEGY_CODE`, `STRATEGY_NAME`, `STRATEGY_DESCRIPTION`
   - `register_strategy_params()` 메서드에 파라미터 정보 추가
   - `__init__()` 생성자 수정
   - `apply()` 메서드에 전략 로직 구현
   - `params` 프로퍼티 업데이트

## 2. 전략 로직 구현

`apply()` 메서드에 전략 로직을 구현하세요. 중요 사항:
- 데이터프레임에 'signal' 컬럼 추가 (1: 매수, -1: 매도, 0: 중립)
- 'position' 컬럼을 통해 거래 시점 감지 (신호 변화)
- 필요한 모든 지표 계산

## 3. 모듈에 전략 등록

새 전략 클래스는 `STRATEGY_CODE` 속성을 가지고 있으면 **자동으로 시스템에 등록**됩니다. 따라서 `__init__.py` 파일을 수정할 필요가 없습니다. 그러나 하위 호환성을 위해 추가할 수도 있습니다:

```python
from .your_strategy_name_strategy import YourStrategyNameStrategy
# ...
__all__ = [
    # ... 
    'YourStrategyNameStrategy',
    # ...
]
```

## 4. 전략 사용

새 전략은 자동으로 시스템에 등록되며, 다음 명령으로 사용 가능한 전략 목록을 확인할 수 있습니다:
```bash
./run.sh --help
```

전략 사용 방법:
```bash
./run.sh --backtest --strategy your_strategy_code --period 3m
```

## 5. 작동 원리

### 전략 자동 발견 과정

1. `StrategyRegistry`는 `src/strategies` 디렉토리에서 모든 전략 클래스를 자동으로 발견합니다.
2. 각 전략 클래스는 `STRATEGY_CODE`를 통해 고유 식별자를 가집니다.
3. CLI 인터페이스는 사용 가능한 모든 전략을 자동으로 인식합니다.
4. 도움말(`./run.sh --help`)에 전략 정보가 자동으로 표시됩니다.
5. **중요**: 전략을 추가해도 `run.sh` 파일을 수정할 필요가 없습니다. 전략 코드는 자동으로 도움말과 CLI에 통합됩니다.

### 전략 파라미터 관리

전략 파라미터는 `register_strategy_params()` 메서드를 통해 중앙에서 관리됩니다:

```python
@classmethod
def register_strategy_params(cls):
    return [
        {
            "name": "window",
            "type": "int",
            "default": 14,
            "description": "기간",
            "min": 2,
            "max": 100
        }
        # 추가 파라미터...
    ]
```

## 예제

### 1. 간단한 모멘텀 전략 예제

```python
class MomentumStrategy(BaseStrategy):
    STRATEGY_CODE = "momentum"
    STRATEGY_NAME = "모멘텀 전략"
    STRATEGY_DESCRIPTION = "N일 기준 가격 변화율을 활용한 모멘텀 전략"
    
    @classmethod
    def register_strategy_params(cls):
        return [
            {
                "name": "window",
                "type": "int",
                "default": 10,
                "description": "모멘텀 계산 기간",
                "min": 1,
                "max": 100
            },
            {
                "name": "threshold",
                "type": "float",
                "default": 0.05,
                "description": "매수/매도 임계값",
                "min": 0.01,
                "max": 0.2
            }
        ]
    
    def __init__(self, window=10, threshold=0.05):
        self._window = window
        self._threshold = threshold
    
    def apply(self, df):
        df = self.validate_data(df).copy()
        
        # 모멘텀 계산 (N일 가격 변화율)
        df['momentum'] = df['close'].pct_change(self._window)
        
        # 신호 생성
        df['signal'] = 0
        df.loc[df['momentum'] > self._threshold, 'signal'] = 1  # 매수
        df.loc[df['momentum'] < -self._threshold, 'signal'] = -1  # 매도
        
        # 거래 시점 감지
        df['position'] = df['signal'].diff()
        
        return df
```

## 문제 해결

- 전략이 등록되지 않는 경우: `STRATEGY_CODE` 설정 확인
- 파라미터 오류: `register_strategy_params()`와 `__init__()` 일치 여부 확인
- 데이터 부족 경고: 각 전략은 `get_min_required_rows()`를 통해 필요한 최소 데이터 행 수를 지정합니다. 데이터가 부족한 경우 시스템은 에러 대신 친화적인 경고 메시지를 표시합니다:
  ```
  ⚠️ 경고: 전략 적용에 최소 35개 행이 필요합니다. 현재: 31
  다음 옵션을 시도해보세요:
    1. 더 긴 기간 사용: -p 3m 또는 -p 6m
    2. 더 짧은 시간 간격 사용: -v minute60 또는 -v minute30
    3. 더 많은 데이터가 필요한 전략이므로 다른 전략을 시도
  ```
  이 경우 다음 해결 방법을 시도해 볼 수 있습니다:
  - 기간 매개변수 확장 (예: `-p 3m` 또는 `-p 6m`)
  - 더 작은 시간 간격 사용 (예: `-v minute60`)
  - 필요한 데이터가 더 적은 다른 전략 시도 