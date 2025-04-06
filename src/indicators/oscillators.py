"""
오실레이터 지표 모듈

RSI, 스토캐스틱, MACD 등 오실레이터 지표를 계산하는 함수를 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

def add_rsi(
    df: pd.DataFrame, 
    window: int = 14,
    column: Optional[str] = None
) -> pd.DataFrame:
    """
    RSI(상대강도지수) 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): RSI 계산 기간
        column (Optional[str]): 계산에 사용할 가격 컬럼 (기본값: 'Close')
        
    Returns:
        pd.DataFrame: RSI가 추가된 데이터프레임
    """
    # 계산에 사용할 컬럼 결정
    if column is None:
        if 'Close' in df.columns:
            column = 'Close'
        elif 'close' in df.columns:
            column = 'close'
        else:
            raise ValueError("가격 컬럼을 찾을 수 없습니다.")
    
    # 데이터 복사
    result_df = df.copy()
    
    # 가격 변화 계산
    delta = result_df[column].diff()
    
    # 상승/하락 구분
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    
    # 평균 상승/하락 계산
    avg_gain = pd.Series(gain).rolling(window=window).mean().values
    avg_loss = pd.Series(loss).rolling(window=window).mean().values
    
    # 첫 번째 값을 계산하기 위한 방법 (Wilder의 방법)
    # 대부분의 첫 번째 평균은 단순 평균이고, 그 이후는 가중 평균을 사용
    for i in range(window, len(delta)):
        avg_gain[i] = (avg_gain[i-1] * (window-1) + gain[i]) / window
        avg_loss[i] = (avg_loss[i-1] * (window-1) + loss[i]) / window
    
    # 상대강도(RS) 계산
    rs = np.where(avg_loss == 0, 100, avg_gain / avg_loss)
    
    # RSI 계산
    rsi = 100 - (100 / (1 + rs))
    
    # 결과 데이터프레임에 추가
    result_df['RSI'] = rsi
    
    return result_df

def add_stochastic(
    df: pd.DataFrame, 
    k_period: int = 14, 
    k_smooth: int = 3, 
    d_period: int = 3
) -> pd.DataFrame:
    """
    스토캐스틱 오실레이터 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        k_period (int): %K 계산 기간
        k_smooth (int): %K 평활화 기간
        d_period (int): %D 계산 기간 (%K의 이동평균 기간)
        
    Returns:
        pd.DataFrame: 스토캐스틱이 추가된 데이터프레임
    """
    # 필요한 컬럼 확인
    if 'High' in df.columns and 'Low' in df.columns and 'Close' in df.columns:
        high, low, close = 'High', 'Low', 'Close'
    elif 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
        high, low, close = 'high', 'low', 'close'
    else:
        raise ValueError("필요한 가격 컬럼(High, Low, Close)을 찾을 수 없습니다.")
    
    # 데이터 복사
    result_df = df.copy()
    
    # %K 계산
    # 최근 k_period 동안의 최고가와 최저가 계산
    low_min = result_df[low].rolling(window=k_period).min()
    high_max = result_df[high].rolling(window=k_period).max()
    
    # %K = (현재가 - 최저가) / (최고가 - 최저가) * 100
    # 분모가 0이 되는 경우를 방지하기 위한 처리
    denominator = high_max - low_min
    denominator = np.where(denominator == 0, 1, denominator)  # 0으로 나누는 것을 방지
    
    stoch_k_raw = ((result_df[close] - low_min) / denominator) * 100
    
    # 평활화된 %K
    result_df['STOCH_K'] = stoch_k_raw.rolling(window=k_smooth).mean()
    
    # %D = %K의 d_period 이동평균
    result_df['STOCH_D'] = result_df['STOCH_K'].rolling(window=d_period).mean()
    
    return result_df

def add_macd(
    df: pd.DataFrame, 
    fast: int = 12, 
    slow: int = 26, 
    signal: int = 9,
    column: Optional[str] = None
) -> pd.DataFrame:
    """
    MACD(이동평균수렴확산) 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        fast (int): 빠른 EMA 기간
        slow (int): 느린 EMA 기간
        signal (int): 시그널 EMA 기간
        column (Optional[str]): 계산에 사용할 가격 컬럼 (기본값: 'Close')
        
    Returns:
        pd.DataFrame: MACD가 추가된 데이터프레임
    """
    # 계산에 사용할 컬럼 결정
    if column is None:
        if 'Close' in df.columns:
            column = 'Close'
        elif 'close' in df.columns:
            column = 'close'
        else:
            raise ValueError("가격 컬럼을 찾을 수 없습니다.")
    
    # 데이터 복사
    result_df = df.copy()
    
    # 빠른 EMA, 느린 EMA 계산
    ema_fast = result_df[column].ewm(span=fast, adjust=False).mean()
    ema_slow = result_df[column].ewm(span=slow, adjust=False).mean()
    
    # MACD 라인 = 빠른 EMA - 느린 EMA
    result_df['MACD'] = ema_fast - ema_slow
    
    # 시그널 라인 = MACD의 EMA
    result_df['MACD_SIGNAL'] = result_df['MACD'].ewm(span=signal, adjust=False).mean()
    
    # MACD 히스토그램 = MACD 라인 - 시그널 라인
    result_df['MACD_HIST'] = result_df['MACD'] - result_df['MACD_SIGNAL']
    
    return result_df

def add_cci(
    df: pd.DataFrame, 
    window: int = 20,
    constant: float = 0.015
) -> pd.DataFrame:
    """
    CCI(상품채널지수) 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): CCI 계산 기간
        constant (float): 보정 상수 (일반적으로 0.015)
        
    Returns:
        pd.DataFrame: CCI가 추가된 데이터프레임
    """
    # 필요한 컬럼 확인
    if 'High' in df.columns and 'Low' in df.columns and 'Close' in df.columns:
        high, low, close = 'High', 'Low', 'Close'
    elif 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
        high, low, close = 'high', 'low', 'close'
    else:
        raise ValueError("필요한 가격 컬럼(High, Low, Close)을 찾을 수 없습니다.")
    
    # 데이터 복사
    result_df = df.copy()
    
    # 전형적 가격 (Typical Price) = (고가 + 저가 + 종가) / 3
    typical_price = (result_df[high] + result_df[low] + result_df[close]) / 3
    
    # 전형적 가격의 이동평균
    tp_ma = typical_price.rolling(window=window).mean()
    
    # 전형적 가격과 이동평균의 차이 (편차)
    mean_deviation = abs(typical_price - tp_ma).rolling(window=window).mean()
    
    # CCI 계산 (전형적 가격이 이동평균에서 얼마나 떨어져 있는지 정규화)
    cci = (typical_price - tp_ma) / (constant * mean_deviation)
    
    # 결과 데이터프레임에 추가
    result_df['CCI'] = cci
    
    return result_df

def add_williams_r(
    df: pd.DataFrame, 
    window: int = 14
) -> pd.DataFrame:
    """
    윌리엄스 %R 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): 윌리엄스 %R 계산 기간
        
    Returns:
        pd.DataFrame: 윌리엄스 %R이 추가된 데이터프레임
    """
    # 필요한 컬럼 확인
    if 'High' in df.columns and 'Low' in df.columns and 'Close' in df.columns:
        high, low, close = 'High', 'Low', 'Close'
    elif 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
        high, low, close = 'high', 'low', 'close'
    else:
        raise ValueError("필요한 가격 컬럼(High, Low, Close)을 찾을 수 없습니다.")
    
    # 데이터 복사
    result_df = df.copy()
    
    # 최근 window 동안의 최고가와 최저가 계산
    highest_high = result_df[high].rolling(window=window).max()
    lowest_low = result_df[low].rolling(window=window).min()
    
    # 윌리엄스 %R = (최고가 - 현재가) / (최고가 - 최저가) * -100
    wr = ((highest_high - result_df[close]) / (highest_high - lowest_low)) * -100
    
    # 결과 데이터프레임에 추가
    result_df['WILLIAMS_R'] = wr
    
    return result_df

def add_momentum(
    df: pd.DataFrame, 
    window: int = 10,
    column: Optional[str] = None
) -> pd.DataFrame:
    """
    모멘텀 지표 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): 모멘텀 계산 기간
        column (Optional[str]): 계산에 사용할 가격 컬럼 (기본값: 'Close')
        
    Returns:
        pd.DataFrame: 모멘텀이 추가된 데이터프레임
    """
    # 계산에 사용할 컬럼 결정
    if column is None:
        if 'Close' in df.columns:
            column = 'Close'
        elif 'close' in df.columns:
            column = 'close'
        else:
            raise ValueError("가격 컬럼을 찾을 수 없습니다.")
    
    # 데이터 복사
    result_df = df.copy()
    
    # 모멘텀 = 현재 가격 - n일 전 가격
    result_df['MOMENTUM'] = result_df[column] - result_df[column].shift(window)
    
    # 모멘텀 % = (현재 가격 / n일 전 가격 - 1) * 100
    result_df['MOMENTUM_PCT'] = (result_df[column] / result_df[column].shift(window) - 1) * 100
    
    return result_df 