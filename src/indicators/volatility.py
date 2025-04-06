"""
변동성 지표 모듈

볼린저 밴드, ATR 등 변동성 관련 기술적 지표 계산 함수를 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union

def bollinger_bands(
    series: pd.Series, 
    window: int = 20, 
    num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    볼린저 밴드 계산
    
    Parameters:
        series (pd.Series): 가격 데이터 시리즈
        window (int): 이동평균 기간 (기본값: 20)
        num_std (float): 표준편차 배수 (기본값: 2.0)
    
    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]: (중간 밴드, 상단 밴드, 하단 밴드)
    """
    # 중간 밴드 (단순 이동평균)
    middle_band = series.rolling(window=window).mean()
    
    # 표준편차
    std_dev = series.rolling(window=window).std()
    
    # 상단 밴드 (중간 밴드 + 표준편차 * 배수)
    upper_band = middle_band + (std_dev * num_std)
    
    # 하단 밴드 (중간 밴드 - 표준편차 * 배수)
    lower_band = middle_band - (std_dev * num_std)
    
    return middle_band, upper_band, lower_band

def add_bollinger_bands(
    df: pd.DataFrame, 
    window: int = 20, 
    num_std: float = 2.0,
    column: Optional[str] = None
) -> pd.DataFrame:
    """
    데이터프레임에 볼린저 밴드 추가
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): 이동평균 기간 (기본값: 20)
        num_std (float): 표준편차 배수 (기본값: 2.0)
        column (Optional[str]): 계산에 사용할 가격 컬럼 (기본값: 'Close')
        
    Returns:
        pd.DataFrame: 볼린저 밴드가 추가된 데이터프레임
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
    
    # 볼린저 밴드 계산
    result_df['BB_MIDDLE'], result_df['BB_UPPER'], result_df['BB_LOWER'] = bollinger_bands(
        result_df[column], window, num_std
    )
    
    # 밴드폭 (Bandwidth) 계산 - 변동성 지표
    result_df['BB_WIDTH'] = (result_df['BB_UPPER'] - result_df['BB_LOWER']) / result_df['BB_MIDDLE']
    
    # %B 계산 - 주가가 밴드 내에서 어디에 위치하는지 나타내는 지표 (0~1 범위)
    result_df['BB_PCT_B'] = (result_df[column] - result_df['BB_LOWER']) / (result_df['BB_UPPER'] - result_df['BB_LOWER'])
    
    return result_df

def atr(
    df: pd.DataFrame, 
    window: int = 14
) -> pd.Series:
    """
    ATR(Average True Range) 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): ATR 계산 기간 (기본값: 14)
    
    Returns:
        pd.Series: 계산된 ATR 시리즈
    """
    # 필요한 컬럼 확인
    if 'High' in df.columns and 'Low' in df.columns and 'Close' in df.columns:
        high, low, close = 'High', 'Low', 'Close'
    elif 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
        high, low, close = 'high', 'low', 'close'
    else:
        raise ValueError("필요한 가격 컬럼(High, Low, Close)을 찾을 수 없습니다.")
    
    # True Range 계산
    tr1 = df[high] - df[low]  # 당일 고가 - 당일 저가
    tr2 = abs(df[high] - df[close].shift())  # 당일 고가 - 전일 종가
    tr3 = abs(df[low] - df[close].shift())  # 당일 저가 - 전일 종가
    
    # 세 가지 TR 중 최대값 선택
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR 계산 (TR의 이동평균)
    return tr.rolling(window=window).mean()

def add_atr(
    df: pd.DataFrame, 
    window: int = 14
) -> pd.DataFrame:
    """
    데이터프레임에 ATR 추가
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): ATR 계산 기간 (기본값: 14)
        
    Returns:
        pd.DataFrame: ATR이 추가된 데이터프레임
    """
    # 데이터 복사
    result_df = df.copy()
    
    # ATR 계산 및 추가
    result_df['ATR'] = atr(df, window)
    
    # ATR 비율 계산 (ATR / 종가의 백분율)
    close_col = 'Close' if 'Close' in df.columns else 'close'
    result_df['ATR_PCT'] = (result_df['ATR'] / result_df[close_col]) * 100
    
    return result_df

def standard_deviation(
    series: pd.Series, 
    window: int = 20
) -> pd.Series:
    """
    가격 변동성 (표준편차) 계산
    
    Parameters:
        series (pd.Series): 가격 데이터 시리즈
        window (int): 계산 기간 (기본값: 20)
    
    Returns:
        pd.Series: 표준편차 시리즈
    """
    return series.rolling(window=window).std()

def add_volatility_indicators(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    여러 변동성 지표 계산을 한 번에 수행
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
    
    Returns:
        pd.DataFrame: 변동성 지표가 추가된 데이터프레임
    """
    result_df = df.copy()
    
    # 볼린저 밴드 추가 (20일, 2 표준편차)
    result_df = add_bollinger_bands(result_df)
    
    # ATR 추가 (14일)
    result_df = add_atr(result_df)
    
    # 일별 변동성 (표준편차) 추가
    close_col = 'Close' if 'Close' in df.columns else 'close'
    result_df['VOLATILITY_20'] = standard_deviation(result_df[close_col], 20)
    result_df['VOLATILITY_50'] = standard_deviation(result_df[close_col], 50)
    
    return result_df

def calculate_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    모든 변동성 지표 계산을 단일 함수로 통합
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
    
    Returns:
        pd.DataFrame: 변동성 지표가 추가된 데이터프레임
    """
    return add_volatility_indicators(df)

def add_keltner_channel(
    df: pd.DataFrame, 
    ema_window: int = 20, 
    atr_window: int = 10, 
    multiplier: float = 2.0
) -> pd.DataFrame:
    """
    켈트너 채널 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        ema_window (int): EMA 계산 기간
        atr_window (int): ATR 계산 기간
        multiplier (float): ATR 승수
        
    Returns:
        pd.DataFrame: 켈트너 채널이 추가된 데이터프레임
    """
    # 필요한 컬럼 확인
    if 'Close' in df.columns:
        close = 'Close'
    elif 'close' in df.columns:
        close = 'close'
    else:
        raise ValueError("종가 컬럼을 찾을 수 없습니다.")
    
    # 데이터 복사
    result_df = df.copy()
    
    # ATR 추가
    result_df = add_atr(result_df, window=atr_window)
    
    # 중간선 (EMA)
    result_df['KC_MIDDLE'] = result_df[close].ewm(span=ema_window, adjust=False).mean()
    
    # 상단선과 하단선
    result_df['KC_UPPER'] = result_df['KC_MIDDLE'] + (multiplier * result_df['ATR'])
    result_df['KC_LOWER'] = result_df['KC_MIDDLE'] - (multiplier * result_df['ATR'])
    
    return result_df

def add_volatility_ratio(
    df: pd.DataFrame, 
    short_window: int = 5, 
    long_window: int = 20,
    column: Optional[str] = None
) -> pd.DataFrame:
    """
    변동성 비율 계산 (단기 변동성 / 장기 변동성)
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        short_window (int): 단기 변동성 기간
        long_window (int): 장기 변동성 기간
        column (Optional[str]): 계산에 사용할 가격 컬럼 (기본값: 'Close')
        
    Returns:
        pd.DataFrame: 변동성 비율이 추가된 데이터프레임
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
    
    # 변동성(표준편차) 계산
    result_df['VOL_SHORT'] = result_df[column].pct_change().rolling(window=short_window).std()
    result_df['VOL_LONG'] = result_df[column].pct_change().rolling(window=long_window).std()
    
    # 변동성 비율 계산
    result_df['VOL_RATIO'] = result_df['VOL_SHORT'] / result_df['VOL_LONG']
    
    return result_df 