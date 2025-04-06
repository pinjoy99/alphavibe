"""
이동평균선 지표 모듈

단순이동평균(SMA), 지수이동평균(EMA) 등 다양한 이동평균선 계산 함수를 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any, Union, Tuple

def sma(series: pd.Series, window: int) -> pd.Series:
    """
    단순이동평균(Simple Moving Average) 계산
    
    Parameters:
        series (pd.Series): 가격 데이터 시리즈
        window (int): 이동평균 기간
        
    Returns:
        pd.Series: 계산된 SMA 시리즈
    """
    return series.rolling(window=window).mean()

def ema(series: pd.Series, window: int) -> pd.Series:
    """
    지수이동평균(Exponential Moving Average) 계산
    
    Parameters:
        series (pd.Series): 가격 데이터 시리즈
        window (int): 이동평균 기간
        
    Returns:
        pd.Series: 계산된 EMA 시리즈
    """
    return series.ewm(span=window, adjust=False).mean()

def wma(series: pd.Series, window: int) -> pd.Series:
    """
    가중이동평균(Weighted Moving Average) 계산
    
    Parameters:
        series (pd.Series): 가격 데이터 시리즈
        window (int): 이동평균 기간
        
    Returns:
        pd.Series: 계산된 WMA 시리즈
    """
    weights = np.arange(1, window + 1)
    return series.rolling(window=window).apply(lambda x: np.sum(weights * x) / weights.sum(), raw=True)

def add_moving_averages(
    df: pd.DataFrame, 
    windows: List[int] = [20, 50, 200], 
    add_ema: bool = True
) -> pd.DataFrame:
    """
    데이터프레임에 이동평균선 추가
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        windows (List[int]): 이동평균 기간 리스트 (기본값: [20, 50, 200])
        add_ema (bool): 지수이동평균선 추가 여부 (기본값: True)
        
    Returns:
        pd.DataFrame: 이동평균선이 추가된 데이터프레임
    """
    # 종가 컬럼 확인
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    # 데이터 복사 (원본 보존)
    result_df = df.copy()
    
    # 단순이동평균선 추가
    for window in windows:
        # SMA 계산
        result_df[f'SMA_{window}'] = sma(result_df[close_col], window)
        
        # EMA 추가 (요청된 경우)
        if add_ema:
            result_df[f'EMA_{window}'] = ema(result_df[close_col], window)
    
    return result_df

def get_ma_crossover_signals(
    df: pd.DataFrame,
    fast_window: int = 20,
    slow_window: int = 50,
    ma_type: str = 'SMA'
) -> pd.DataFrame:
    """
    이동평균선 크로스오버 신호 계산
    
    Parameters:
        df (pd.DataFrame): 이동평균선이 포함된 데이터프레임
        fast_window (int): 단기 이동평균선 기간
        slow_window (int): 장기 이동평균선 기간
        ma_type (str): 이동평균선 유형 ('SMA' 또는 'EMA')
        
    Returns:
        pd.DataFrame: 크로스오버 신호가 추가된 데이터프레임
    """
    # 복사본 생성
    result_df = df.copy()
    
    # 필요한 이동평균선 컬럼 확인
    fast_col = f'{ma_type}_{fast_window}'
    slow_col = f'{ma_type}_{slow_window}'
    
    if fast_col not in result_df.columns or slow_col not in result_df.columns:
        raise ValueError(f"요청된 이동평균선 컬럼 없음: {fast_col}, {slow_col}")
    
    # 크로스오버 신호 계산
    # 1: 골든 크로스 (단기선이 장기선 위로 교차)
    # -1: 데드 크로스 (단기선이 장기선 아래로 교차)
    # 0: 크로스 없음
    
    # 이전 상태와 현재 상태 비교
    result_df['prev_diff'] = (result_df[fast_col].shift(1) - result_df[slow_col].shift(1))
    result_df['curr_diff'] = (result_df[fast_col] - result_df[slow_col])
    
    # 크로스오버 조건 확인
    result_df['crossover'] = 0
    result_df.loc[(result_df['prev_diff'] <= 0) & (result_df['curr_diff'] > 0), 'crossover'] = 1  # 골든 크로스
    result_df.loc[(result_df['prev_diff'] >= 0) & (result_df['curr_diff'] < 0), 'crossover'] = -1  # 데드 크로스
    
    # 임시 컬럼 삭제
    result_df = result_df.drop(['prev_diff', 'curr_diff'], axis=1)
    
    return result_df

def calculate_price_to_ma_ratio(
    df: pd.DataFrame,
    ma_window: int = 200,
    ma_type: str = 'SMA'
) -> pd.DataFrame:
    """
    가격/이동평균선 비율 계산 (추세 강도 지표)
    
    Parameters:
        df (pd.DataFrame): 이동평균선이 포함된 데이터프레임
        ma_window (int): 이동평균선 기간
        ma_type (str): 이동평균선 유형 ('SMA' 또는 'EMA')
        
    Returns:
        pd.DataFrame: 비율이 추가된 데이터프레임
    """
    # 복사본 생성
    result_df = df.copy()
    
    # 종가 컬럼 확인
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    # 이동평균선 컬럼
    ma_col = f'{ma_type}_{ma_window}'
    
    if ma_col not in result_df.columns:
        raise ValueError(f"요청된 이동평균선 컬럼 없음: {ma_col}")
    
    # 가격/이동평균선 비율 계산
    result_df[f'PRICE_TO_MA_{ma_window}'] = result_df[close_col] / result_df[ma_col]
    
    return result_df

def calculate_moving_averages(df: pd.DataFrame, ma_types: List[str] = ['sma', 'ema'], windows: List[int] = [5, 10, 20, 50, 200]) -> pd.DataFrame:
    """
    여러 유형의 이동평균선을 한 번에 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        ma_types (List[str]): 이동평균 유형 목록 (예: ['sma', 'ema', 'wma'])
        windows (List[int]): 이동평균 기간 목록
        
    Returns:
        pd.DataFrame: 이동평균선이 추가된 데이터프레임
    """
    result_df = df.copy()
    
    # 종가 컬럼 확인
    close_col = 'Close' if 'Close' in df.columns else 'close'
    
    # 각 이동평균 유형 및 기간에 대해 계산
    for ma_type in ma_types:
        for window in windows:
            if ma_type.lower() == 'sma':
                result_df[f'sma_{window}'] = sma(result_df[close_col], window)
            elif ma_type.lower() == 'ema':
                result_df[f'ema_{window}'] = ema(result_df[close_col], window)
            elif ma_type.lower() == 'wma':
                result_df[f'wma_{window}'] = wma(result_df[close_col], window)
    
    return result_df 