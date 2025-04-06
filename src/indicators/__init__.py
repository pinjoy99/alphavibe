"""
기술적 지표 계산 모듈

주가 데이터에 대한 다양한 기술적 지표를 계산하는 함수를 제공합니다.
전략 구현과 분석 모드에서 모두 사용됩니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from src.indicators.moving_averages import add_moving_averages
from src.indicators.oscillators import add_rsi, add_stochastic, add_macd
from src.indicators.volatility import add_bollinger_bands, add_atr
from src.indicators.support_resistance import find_support_resistance_levels

# 이동평균선 관련 지표
from .moving_averages import (
    sma,
    ema,
    wma,
    calculate_moving_averages
)

# 볼린저 밴드 관련 지표
from .volatility import (
    bollinger_bands,
    atr,
    standard_deviation,
    calculate_volatility_indicators
)

# 모멘텀 지표
from .momentum import (
    rsi,
    stochastic,
    macd,
    calculate_momentum_indicators
)

# 추세 지표
from .trend import (
    adx,
    aroon,
    ichimoku,
    calculate_trend_indicators
)

# 가격 패턴
from .patterns import (
    support_resistance,
    fibonacci_levels,
    calculate_price_patterns
)

# 통합 지표 계산
from .calculator import calculate_all_indicators

def calculate_indicators(
    df: pd.DataFrame,
    ma_windows: List[int] = [20, 50, 200],
    add_ema: bool = True,
    volatility_window: int = 20,
    rsi_window: int = 14,
    macd_params: Tuple[int, int, int] = (12, 26, 9),
    stoch_params: Tuple[int, int, int] = (14, 3, 3)
) -> pd.DataFrame:
    """
    주가 데이터에 여러 기술적 지표를 계산하여 추가
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        ma_windows (List[int]): 이동평균 계산 기간 목록
        add_ema (bool): EMA 추가 여부
        volatility_window (int): 볼린저 밴드 및 ATR 계산 기간
        rsi_window (int): RSI 계산 기간
        macd_params (Tuple[int, int, int]): MACD 계산 파라미터 (단기, 장기, 시그널)
        stoch_params (Tuple[int, int, int]): 스토캐스틱 계산 파라미터 (%K기간, %K 평활화, %D 기간)
        
    Returns:
        pd.DataFrame: 지표가 추가된 데이터프레임
    """
    # 컬럼명 표준화 (필요한 경우)
    if not all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
        # 소문자로 되어있는 경우
        rename_cols = {
            'open': 'Open', 'high': 'High', 'low': 'Low', 
            'close': 'Close', 'volume': 'Volume'
        }
        # 이미 있는 컬럼에 대해서만 이름 변경
        df = df.rename(columns={k: v for k, v in rename_cols.items() if k in df.columns})
    
    # 데이터 복사 (원본 보존)
    result_df = df.copy()
    
    # 결측치 제거 (필요한 경우)
    result_df.dropna(inplace=True)
    
    # 1. 이동평균선 추가
    result_df = add_moving_averages(result_df, ma_windows, add_ema)
    
    # 2. 볼린저 밴드 추가
    result_df = add_bollinger_bands(result_df, window=volatility_window)
    
    # 3. ATR 추가
    result_df = add_atr(result_df, window=volatility_window)
    
    # 4. RSI 추가
    result_df = add_rsi(result_df, window=rsi_window)
    
    # 5. MACD 추가
    result_df = add_macd(result_df, fast=macd_params[0], slow=macd_params[1], signal=macd_params[2])
    
    # 6. 스토캐스틱 추가
    result_df = add_stochastic(result_df, k_period=stoch_params[0], k_smooth=stoch_params[1], d_period=stoch_params[2])
    
    return result_df 