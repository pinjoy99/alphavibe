"""
모멘텀 지표 계산 모듈

RSI, MACD, 스토캐스틱 등 모멘텀 관련 기술적 지표 계산 함수를 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union

def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """
    RSI(Relative Strength Index) 계산
    
    Parameters:
        series (pd.Series): 가격 데이터 시리즈
        window (int): RSI 계산 기간 (기본값: 14)
    
    Returns:
        pd.Series: 계산된 RSI 시리즈
    """
    # 데이터 유효성 검사
    if len(series) <= window:
        print(f"경고: RSI 계산에 필요한 데이터가 부족합니다. 최소 {window+1}개 필요, 현재 {len(series)}개")
        return pd.Series(np.nan, index=series.index)
    
    # 가격 변화량 계산
    delta = series.diff()
    
    # 상승분과 하락분 구분
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # 평균 상승/하락 계산 (EMA 방식)
    avg_gain = gain.ewm(com=window-1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window-1, min_periods=window).mean()
    
    # RS(Relative Strength) 계산 - 0으로 나누는 오류 방지
    rs = avg_gain / np.maximum(avg_loss, 1e-10)  # 분모가 0이면 작은 값으로 대체
    
    # RSI 계산
    rsi_values = 100 - (100 / (1 + rs))
    
    # 결과 유효성 검사
    if rsi_values.isna().all():
        print("경고: RSI 계산 결과가 유효하지 않습니다.")
    
    return rsi_values

def macd(series: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD(Moving Average Convergence Divergence) 계산
    
    Parameters:
        series (pd.Series): 가격 데이터 시리즈
        fast_period (int): 단기 EMA 기간 (기본값: 12)
        slow_period (int): 장기 EMA 기간 (기본값: 26)
        signal_period (int): 시그널 라인 기간 (기본값: 9)
    
    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]: (MACD 라인, 시그널 라인, 히스토그램)
    """
    # 단기 및 장기 EMA 계산
    fast_ema = series.ewm(span=fast_period, adjust=False).mean()
    slow_ema = series.ewm(span=slow_period, adjust=False).mean()
    
    # MACD 라인 = 단기 EMA - 장기 EMA
    macd_line = fast_ema - slow_ema
    
    # 시그널 라인 = MACD의 EMA
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    
    # 히스토그램 = MACD 라인 - 시그널 라인
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3, slowing: int = 3) -> Tuple[pd.Series, pd.Series]:
    """
    스토캐스틱 오실레이터 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        k_period (int): %K 기간 (기본값: 14)
        d_period (int): %D 기간 (기본값: 3)
        slowing (int): 슬로잉 기간 (기본값: 3)
    
    Returns:
        Tuple[pd.Series, pd.Series]: (%K, %D)
    """
    # 최근 k_period 동안의 최고가 및 최저가 계산
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()
    
    # %K 계산
    k_fast = 100 * ((df['close'] - low_min) / (high_max - low_min))
    
    # 슬로잉 적용 (이동평균)
    k = k_fast.rolling(window=slowing).mean()
    
    # %D 계산 (K의 이동평균)
    d = k.rolling(window=d_period).mean()
    
    return k, d

def calculate_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    여러 모멘텀 지표 계산을 한 번에 수행
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
    
    Returns:
        pd.DataFrame: 모멘텀 지표가 추가된 데이터프레임
    """
    result_df = df.copy()
    
    # RSI 계산
    result_df['rsi'] = rsi(result_df['close'])
    
    # MACD 계산
    result_df['macd'], result_df['signal_line'], result_df['macd_hist'] = macd(result_df['close'])
    
    # 스토캐스틱 계산
    result_df['stoch_k'], result_df['stoch_d'] = stochastic(result_df)
    
    return result_df 