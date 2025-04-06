"""
추세 지표 계산 모듈

ADX, Aroon, Ichimoku 등 추세 관련 기술적 지표 계산 함수를 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union

def adx(df: pd.DataFrame, window: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    ADX(Average Directional Index) 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): ADX 계산 기간 (기본값: 14)
    
    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]: (ADX, +DI, -DI)
    """
    # 1. TR(True Range) 계산
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # 2. +DM, -DM 계산
    up_move = df['high'] - df['high'].shift()
    down_move = df['low'].shift() - df['low']
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # 3. 평활화된 +DM, -DM, TR 계산
    smoothed_plus_dm = pd.Series(plus_dm).rolling(window=window).sum()
    smoothed_minus_dm = pd.Series(minus_dm).rolling(window=window).sum()
    smoothed_tr = true_range.rolling(window=window).sum()
    
    # 4. +DI, -DI 계산
    plus_di = 100 * (smoothed_plus_dm / smoothed_tr)
    minus_di = 100 * (smoothed_minus_dm / smoothed_tr)
    
    # 5. DX(Directional Index) 계산
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    
    # 6. ADX 계산 (DX의 평균)
    adx_values = dx.rolling(window=window).mean()
    
    return adx_values, plus_di, minus_di

def aroon(df: pd.DataFrame, window: int = 25) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Aroon 지표 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): Aroon 계산 기간 (기본값: 25)
    
    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]: (Aroon Up, Aroon Down, Aroon Oscillator)
    """
    # Aroon Up: 기간 내 최고가까지의 기간 비율
    aroon_up = 100 * df['high'].rolling(window=window).apply(
        lambda x: window - x.argmax(), raw=True
    ) / window
    
    # Aroon Down: 기간 내 최저가까지의 기간 비율
    aroon_down = 100 * df['low'].rolling(window=window).apply(
        lambda x: window - x.argmin(), raw=True
    ) / window
    
    # Aroon Oscillator: Aroon Up - Aroon Down
    aroon_osc = aroon_up - aroon_down
    
    return aroon_up, aroon_down, aroon_osc

def ichimoku(df: pd.DataFrame, tenkan_period: int = 9, kijun_period: int = 26, 
             senkou_b_period: int = 52, displacement: int = 26) -> Dict[str, pd.Series]:
    """
    Ichimoku Cloud 지표 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        tenkan_period (int): 전환선 기간 (기본값: 9)
        kijun_period (int): 기준선 기간 (기본값: 26)
        senkou_b_period (int): 선행스팬 B 기간 (기본값: 52)
        displacement (int): 선행스팬 이동 기간 (기본값: 26)
    
    Returns:
        Dict[str, pd.Series]: Ichimoku 구성 요소
    """
    # 1. 전환선 (Tenkan-sen) = (최고가 + 최저가) / 2 (for tenkan_period)
    tenkan_sen = (df['high'].rolling(window=tenkan_period).max() + 
                 df['low'].rolling(window=tenkan_period).min()) / 2
    
    # 2. 기준선 (Kijun-sen) = (최고가 + 최저가) / 2 (for kijun_period)
    kijun_sen = (df['high'].rolling(window=kijun_period).max() + 
                df['low'].rolling(window=kijun_period).min()) / 2
    
    # 3. 후행스팬 (Chikou Span) = 현재 종가를 displacement 기간만큼 과거로 이동
    chikou_span = df['close'].shift(-displacement)
    
    # 4. 선행스팬 A (Senkou Span A) = (전환선 + 기준선) / 2를 displacement 기간만큼 미래로 이동
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
    
    # 5. 선행스팬 B (Senkou Span B) = (최고가 + 최저가) / 2 (for senkou_b_period)를 displacement 기간만큼 미래로 이동
    senkou_span_b = ((df['high'].rolling(window=senkou_b_period).max() + 
                     df['low'].rolling(window=senkou_b_period).min()) / 2).shift(displacement)
    
    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'chikou_span': chikou_span,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b
    }

def calculate_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    여러 추세 지표 계산을 한 번에 수행
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
    
    Returns:
        pd.DataFrame: 추세 지표가 추가된 데이터프레임
    """
    result_df = df.copy()
    
    # ADX 계산
    result_df['adx'], result_df['plus_di'], result_df['minus_di'] = adx(result_df)
    
    # Aroon 계산
    result_df['aroon_up'], result_df['aroon_down'], result_df['aroon_osc'] = aroon(result_df)
    
    # Ichimoku 계산
    ichimoku_values = ichimoku(result_df)
    for key, value in ichimoku_values.items():
        result_df[key] = value
    
    return result_df 