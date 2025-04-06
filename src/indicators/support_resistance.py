"""
지지/저항선 지표 모듈

주가 데이터에서 지지선과 저항선을 계산하는 함수를 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from scipy.signal import argrelextrema

def find_support_resistance_levels(
    df: pd.DataFrame, 
    window: int = 10,
    min_distance: int = 5,
    threshold_pct: float = 1.0,
    max_levels: int = 3
) -> Tuple[List[float], List[float]]:
    """
    주가 데이터에서 주요 지지/저항 수준 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        window (int): 피봇 포인트를 찾기 위한 기간 (최소치/최대치를 식별하기 위한 좌우 비교 범위)
        min_distance (int): 서로 다른 수준 간의 최소 가격 거리 (%)
        threshold_pct (float): 고려할 수준의 최소 가격 거리 (%)
        max_levels (int): 반환할 최대 지지/저항 수준 수
        
    Returns:
        Tuple[List[float], List[float]]: (지지선 리스트, 저항선 리스트)
    """
    # 필요한 컬럼 확인
    if 'High' in df.columns and 'Low' in df.columns and 'Close' in df.columns:
        high, low, close = 'High', 'Low', 'Close'
    elif 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
        high, low, close = 'high', 'low', 'close'
    else:
        raise ValueError("필요한 가격 컬럼(High, Low, Close)을 찾을 수 없습니다.")
    
    # 데이터프레임이 비어있거나 너무 작은 경우 빈 결과 반환
    if df.empty or len(df) < window * 2:
        return [], []
    
    try:
        # 현재 가격 가져오기
        current_price = df[close].iloc[-1]
        
        # 지역 최소값과 최대값 찾기
        highs = argrelextrema(df[high].values, np.greater_equal, order=window)[0]
        lows = argrelextrema(df[low].values, np.less_equal, order=window)[0]
        
        # 저항 수준 (최근 데이터에서 먼저 선택)
        resistance_levels = []
        for idx in reversed(highs):
            if idx < len(df):  # 인덱스 범위 체크
                level = df[high].iloc[idx]
                # 현재 가격보다 높은 수준만 저항으로 간주
                if level > current_price * (1 + threshold_pct / 100):
                    # 이미 식별된 수준과 충분히 떨어져 있는지 확인
                    if not any(abs(level / r - 1) * 100 < min_distance for r in resistance_levels):
                        resistance_levels.append(level)
                        if len(resistance_levels) >= max_levels:
                            break
        
        # 지지 수준 (최근 데이터에서 먼저 선택)
        support_levels = []
        for idx in reversed(lows):
            if idx < len(df):  # 인덱스 범위 체크
                level = df[low].iloc[idx]
                # 현재 가격보다 낮은 수준만 지지로 간주
                if level < current_price * (1 - threshold_pct / 100):
                    # 이미 식별된 수준과 충분히 떨어져 있는지 확인
                    if not any(abs(level / s - 1) * 100 < min_distance for s in support_levels):
                        support_levels.append(level)
                        if len(support_levels) >= max_levels:
                            break
    except Exception as e:
        print(f"지지/저항선 계산 중 오류 발생: {e}")
        return [], []
    
    return sorted(support_levels), sorted(resistance_levels)

def find_pivot_points(
    df: pd.DataFrame, 
    pivot_type: str = 'standard'
) -> Dict[str, float]:
    """
    피봇 포인트 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임 (마지막 행이 가장 최근 데이터여야 함)
        pivot_type (str): 피봇 포인트 유형 ('standard', 'fibonacci', 'woodie', 'camarilla')
        
    Returns:
        Dict[str, float]: 피봇 포인트와 지지/저항 수준
    """
    # 필요한 컬럼 확인
    if 'High' in df.columns and 'Low' in df.columns and 'Close' in df.columns:
        high, low, close = 'High', 'Low', 'Close'
    elif 'high' in df.columns and 'low' in df.columns and 'close' in df.columns:
        high, low, close = 'high', 'low', 'close'
    else:
        raise ValueError("필요한 가격 컬럼(High, Low, Close)을 찾을 수 없습니다.")
    
    # 피봇 계산에 필요한 가격 가져오기
    if len(df) < 2:
        raise ValueError("피봇 포인트 계산에는 최소 2개 이상의 데이터 포인트가 필요합니다.")
        
    prev_high = df[high].iloc[-2]
    prev_low = df[low].iloc[-2]
    prev_close = df[close].iloc[-2]
    
    # 결과 저장용 딕셔너리
    result = {}
    
    # 표준 피봇 포인트 계산
    if pivot_type == 'standard':
        pp = (prev_high + prev_low + prev_close) / 3
        
        r1 = (2 * pp) - prev_low
        r2 = pp + (prev_high - prev_low)
        r3 = r1 + (prev_high - prev_low)
        
        s1 = (2 * pp) - prev_high
        s2 = pp - (prev_high - prev_low)
        s3 = s1 - (prev_high - prev_low)
        
        result = {
            'PP': pp,
            'R1': r1, 'R2': r2, 'R3': r3,
            'S1': s1, 'S2': s2, 'S3': s3
        }
    
    # 피보나치 피봇 포인트 계산
    elif pivot_type == 'fibonacci':
        pp = (prev_high + prev_low + prev_close) / 3
        
        r1 = pp + 0.382 * (prev_high - prev_low)
        r2 = pp + 0.618 * (prev_high - prev_low)
        r3 = pp + (prev_high - prev_low)
        
        s1 = pp - 0.382 * (prev_high - prev_low)
        s2 = pp - 0.618 * (prev_high - prev_low)
        s3 = pp - (prev_high - prev_low)
        
        result = {
            'PP': pp,
            'R1': r1, 'R2': r2, 'R3': r3,
            'S1': s1, 'S2': s2, 'S3': s3
        }
    
    # 우디 피봇 포인트 계산
    elif pivot_type == 'woodie':
        pp = (prev_high + prev_low + 2 * prev_close) / 4
        
        r1 = (2 * pp) - prev_low
        r2 = pp + (prev_high - prev_low)
        
        s1 = (2 * pp) - prev_high
        s2 = pp - (prev_high - prev_low)
        
        result = {
            'PP': pp,
            'R1': r1, 'R2': r2,
            'S1': s1, 'S2': s2
        }
    
    # 카마릴라 피봇 포인트 계산
    elif pivot_type == 'camarilla':
        pp = (prev_high + prev_low + prev_close) / 3
        
        r1 = prev_close + (prev_high - prev_low) * 1.1 / 12
        r2 = prev_close + (prev_high - prev_low) * 1.1 / 6
        r3 = prev_close + (prev_high - prev_low) * 1.1 / 4
        r4 = prev_close + (prev_high - prev_low) * 1.1 / 2
        
        s1 = prev_close - (prev_high - prev_low) * 1.1 / 12
        s2 = prev_close - (prev_high - prev_low) * 1.1 / 6
        s3 = prev_close - (prev_high - prev_low) * 1.1 / 4
        s4 = prev_close - (prev_high - prev_low) * 1.1 / 2
        
        result = {
            'PP': pp,
            'R1': r1, 'R2': r2, 'R3': r3, 'R4': r4,
            'S1': s1, 'S2': s2, 'S3': s3, 'S4': s4
        }
    
    else:
        raise ValueError("지원되지 않는 피봇 포인트 유형입니다. 'standard', 'fibonacci', 'woodie', 'camarilla' 중 하나를 사용하세요.")
    
    return result

def is_price_at_support(
    df: pd.DataFrame,
    price: Optional[float] = None,
    window: int = 10,
    threshold_pct: float = 1.0
) -> bool:
    """
    현재 가격이 지지선에 있는지 확인
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        price (Optional[float]): 확인할 가격 (기본값: 현재 종가)
        window (int): 지지선을 확인할 데이터 기간
        threshold_pct (float): 지지선으로 간주할 최대 거리 (%)
        
    Returns:
        bool: 가격이 지지선 근처에 있으면 True, 아니면 False
    """
    # 필요한 컬럼 확인
    if 'Low' in df.columns and 'Close' in df.columns:
        low, close = 'Low', 'Close'
    elif 'low' in df.columns and 'close' in df.columns:
        low, close = 'low', 'close'
    else:
        raise ValueError("필요한 가격 컬럼(Low, Close)을 찾을 수 없습니다.")
    
    # 확인할 가격이 지정되지 않은 경우 현재 종가 사용
    if price is None:
        price = df[close].iloc[-1]
    
    # 지역 최소값 찾기
    lows = df[low].rolling(window=window, center=True).min().iloc[-window:]
    
    # 지지선 근처에 있는지 확인 (지정된 임계값 내에서)
    for support_level in lows:
        if abs(price / support_level - 1) * 100 <= threshold_pct:
            return True
    
    return False

def is_price_at_resistance(
    df: pd.DataFrame,
    price: Optional[float] = None,
    window: int = 10,
    threshold_pct: float = 1.0
) -> bool:
    """
    현재 가격이 저항선에 있는지 확인
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        price (Optional[float]): 확인할 가격 (기본값: 현재 종가)
        window (int): 저항선을 확인할 데이터 기간
        threshold_pct (float): 저항선으로 간주할 최대 거리 (%)
        
    Returns:
        bool: 가격이 저항선 근처에 있으면 True, 아니면 False
    """
    # 필요한 컬럼 확인
    if 'High' in df.columns and 'Close' in df.columns:
        high, close = 'High', 'Close'
    elif 'high' in df.columns and 'close' in df.columns:
        high, close = 'high', 'close'
    else:
        raise ValueError("필요한 가격 컬럼(High, Close)을 찾을 수 없습니다.")
    
    # 확인할 가격이 지정되지 않은 경우 현재 종가 사용
    if price is None:
        price = df[close].iloc[-1]
    
    # 지역 최대값 찾기
    highs = df[high].rolling(window=window, center=True).max().iloc[-window:]
    
    # 저항선 근처에 있는지 확인 (지정된 임계값 내에서)
    for resistance_level in highs:
        if abs(price / resistance_level - 1) * 100 <= threshold_pct:
            return True
    
    return False 