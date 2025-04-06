"""
가격 패턴 분석 모듈

지지선/저항선, 피보나치 리트레이스먼트 등 가격 패턴 관련 함수를 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union
from scipy.signal import argrelextrema
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def support_resistance(df: pd.DataFrame, window: int = 10, threshold: float = 0.02) -> Tuple[List[float], List[float]]:
    """
    지지선과 저항선 레벨 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): 고점/저점 검색 윈도우 크기 (기본값: 10)
        threshold (float): 유사 레벨 병합 임계값 (기본값: 0.02)
    
    Returns:
        Tuple[List[float], List[float]]: (지지선 레벨 목록, 저항선 레벨 목록)
    """
    # scipy의 argrelextrema 함수로 로컬 최소/최대값 인덱스 찾기
    min_idx = argrelextrema(df['low'].values, np.less, order=window)[0]
    max_idx = argrelextrema(df['high'].values, np.greater, order=window)[0]
    
    # 해당 인덱스의 고가/저가 추출
    support_levels = [df['low'].iloc[i] for i in min_idx]
    resistance_levels = [df['high'].iloc[i] for i in max_idx]
    
    # 유사한 레벨 병합
    support_levels = merge_levels(support_levels, threshold)
    resistance_levels = merge_levels(resistance_levels, threshold)
    
    return support_levels, resistance_levels

def merge_levels(levels: List[float], threshold: float) -> List[float]:
    """
    유사한 가격 레벨 병합
    
    Parameters:
        levels (List[float]): 가격 레벨 목록
        threshold (float): 병합 임계값 (상대차이)
        
    Returns:
        List[float]: 병합된 가격 레벨 목록
    """
    if not levels:
        return []
    
    # 가격 오름차순 정렬
    sorted_levels = sorted(levels)
    merged_levels = [sorted_levels[0]]
    
    for level in sorted_levels[1:]:
        # 직전 레벨과의 상대적 차이 계산
        prev_level = merged_levels[-1]
        rel_diff = abs(level - prev_level) / prev_level
        
        # 임계값보다 차이가 크면 새 레벨로 추가
        if rel_diff > threshold:
            merged_levels.append(level)
    
    return merged_levels

def fibonacci_levels(df: pd.DataFrame, is_uptrend: bool = True) -> Dict[str, float]:
    """
    피보나치 리트레이스먼트 레벨 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        is_uptrend (bool): 상승추세 여부 (하락추세는 False)
    
    Returns:
        Dict[str, float]: 피보나치 리트레이스먼트 레벨
    """
    if is_uptrend:
        # 상승추세: 최저점에서 최고점까지
        low_price = df['low'].min()
        high_price = df['high'].max()
    else:
        # 하락추세: 최고점에서 최저점까지
        high_price = df['high'].max()
        low_price = df['low'].min()
    
    # 가격 차이
    diff = high_price - low_price
    
    # 피보나치 레벨 계산
    levels = {
        '0.0': low_price if is_uptrend else high_price,
        '0.236': low_price + 0.236 * diff if is_uptrend else high_price - 0.236 * diff,
        '0.382': low_price + 0.382 * diff if is_uptrend else high_price - 0.382 * diff,
        '0.5': low_price + 0.5 * diff if is_uptrend else high_price - 0.5 * diff,
        '0.618': low_price + 0.618 * diff if is_uptrend else high_price - 0.618 * diff,
        '0.786': low_price + 0.786 * diff if is_uptrend else high_price - 0.786 * diff,
        '1.0': high_price if is_uptrend else low_price
    }
    
    return levels

def pivot_points(df: pd.DataFrame, method: str = 'standard') -> Dict[str, pd.Series]:
    """
    일별 피봇 포인트 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        method (str): 피봇 포인트 계산 방식 ('standard', 'fibonacci', 'woodie')
    
    Returns:
        Dict[str, pd.Series]: 피봇 포인트와 지지/저항 레벨
    """
    # 최근 바의 OHLC 가져오기
    high = df['high'].shift(1)
    low = df['low'].shift(1)
    close = df['close'].shift(1)
    open_price = df['open']
    
    if method == 'standard':
        # 표준 피봇 포인트
        pp = (high + low + close) / 3
        r1 = (2 * pp) - low
        s1 = (2 * pp) - high
        r2 = pp + (high - low)
        s2 = pp - (high - low)
        r3 = pp + 2 * (high - low)
        s3 = pp - 2 * (high - low)
        
    elif method == 'fibonacci':
        # 피보나치 피봇 포인트
        pp = (high + low + close) / 3
        r1 = pp + 0.382 * (high - low)
        s1 = pp - 0.382 * (high - low)
        r2 = pp + 0.618 * (high - low)
        s2 = pp - 0.618 * (high - low)
        r3 = pp + 1.0 * (high - low)
        s3 = pp - 1.0 * (high - low)
        
    elif method == 'woodie':
        # 우디 피봇 포인트
        pp = (high + low + 2 * close) / 4
        r1 = (2 * pp) - low
        s1 = (2 * pp) - high
        r2 = pp + (high - low)
        s2 = pp - (high - low)
        r3 = r1 + (high - low)
        s3 = s1 - (high - low)
        
    else:
        raise ValueError(f"지원되지 않는 피봇 포인트 방식: {method}")
    
    return {
        'pp': pp,
        'r1': r1,
        's1': s1,
        'r2': r2,
        's2': s2,
        'r3': r3,
        's3': s3
    }

def calculate_price_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    가격 패턴 분석 수행
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
    
    Returns:
        pd.DataFrame: 패턴 분석 결과가 추가된 데이터프레임
    """
    result_df = df.copy()
    
    # 현재 추세 판단 (최근 20일 종가 기울기)
    slope = np.polyfit(np.arange(min(20, len(df))), 
                      result_df['close'].tail(min(20, len(df))), 1)[0]
    is_uptrend = slope > 0
    
    # 피보나치 레벨 계산
    fib_levels = fibonacci_levels(df, is_uptrend)
    
    # 표준 피봇 포인트 계산
    pivot_levels = pivot_points(df)
    
    # 지지선/저항선 레벨 계산
    support_levels, resistance_levels = support_resistance(df)
    
    # 결과 df에 중요 레벨 추가 (직접 추가하지 않고 별도 변수로 저장)
    result_df.attrs['support_levels'] = support_levels
    result_df.attrs['resistance_levels'] = resistance_levels
    result_df.attrs['fibonacci_levels'] = fib_levels
    result_df.attrs['is_uptrend'] = is_uptrend
    
    # 피봇 포인트를 각 행에 추가
    for key, value in pivot_levels.items():
        result_df[f'pivot_{key}'] = value
    
    return result_df 