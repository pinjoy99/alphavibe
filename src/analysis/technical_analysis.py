"""
기술적 분석 모듈

기술적 지표를 해석하고 분석하는 함수를 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

def analyze_technical_indicators(df: pd.DataFrame) -> Dict[str, str]:
    """
    기술적 지표를 분석하여 해석 결과 반환
    
    Parameters:
        df (pd.DataFrame): 지표가 계산된 데이터프레임
        
    Returns:
        Dict[str, str]: 지표별 분석 결과
    """
    result = {}
    
    # 최신 데이터
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest
    
    # 1. RSI 분석
    if 'RSI' in df.columns:
        rsi_value = latest['RSI']
        if rsi_value > 70:
            result['RSI'] = f"과매수 구간 ({rsi_value:.1f})"
        elif rsi_value < 30:
            result['RSI'] = f"과매도 구간 ({rsi_value:.1f})"
        elif rsi_value >= 50:
            result['RSI'] = f"상승 추세 ({rsi_value:.1f})"
        else:
            result['RSI'] = f"하락 추세 ({rsi_value:.1f})"
    
    # 2. MACD 분석
    if all(col in df.columns for col in ['MACD', 'MACD_SIGNAL']):
        macd_value = latest['MACD']
        signal_value = latest['MACD_SIGNAL']
        hist = macd_value - signal_value
        
        # 현재 MACD 상태
        if hist > 0 and hist > df['MACD'].iloc[-2] - df['MACD_SIGNAL'].iloc[-2]:
            result['MACD'] = f"상승 추세 강화 중 ({macd_value:.2f})"
        elif hist > 0:
            result['MACD'] = f"상승 추세 ({macd_value:.2f})"
        elif hist < 0 and hist < df['MACD'].iloc[-2] - df['MACD_SIGNAL'].iloc[-2]:
            result['MACD'] = f"하락 추세 강화 중 ({macd_value:.2f})"
        else:
            result['MACD'] = f"하락 추세 ({macd_value:.2f})"
    
    # 3. 볼린저 밴드 분석
    bb_cols = ['BB_UPPER', 'BB_LOWER', 'BB_MID']
    bb_aliases = {'BB_UPPER': 'upper_band', 'BB_LOWER': 'lower_band', 'BB_MID': 'middle_band'}
    
    # 컬럼명 확인 (대소문자 차이가 있을 수 있음)
    for orig_col, alias in bb_aliases.items():
        if orig_col in df.columns:
            bb_aliases[orig_col] = orig_col
        elif alias in df.columns:
            bb_aliases[orig_col] = alias
    
    if all(alias in df.columns for alias in bb_aliases.values()):
        price = latest['close'] if 'close' in df.columns else latest['Close']
        upper = latest[bb_aliases['BB_UPPER']]
        lower = latest[bb_aliases['BB_LOWER']]
        middle = latest[bb_aliases['BB_MID']]
        
        # 볼린저 밴드 위치
        if price > upper:
            result['볼린저 밴드'] = f"상단 돌파 (과매수 가능성)"
        elif price < lower:
            result['볼린저 밴드'] = f"하단 돌파 (과매도 가능성)"
        elif price > middle:
            result['볼린저 밴드'] = f"상단 밴드 접근 중"
        else:
            result['볼린저 밴드'] = f"하단 밴드 접근 중"
    
    # 4. 이동평균선 분석
    ma_indicators = {
        'SMA_20': 'SMA 20',
        'SMA_50': 'SMA 50',
        'SMA_200': 'SMA 200',
        'EMA_20': 'EMA 20',
        'EMA_50': 'EMA 50'
    }
    
    price = latest['close'] if 'close' in df.columns else latest['Close']
    ma_status = []
    
    for indicator, label in ma_indicators.items():
        if indicator in df.columns and not pd.isna(latest[indicator]):
            ma_value = latest[indicator]
            if price > ma_value:
                ma_status.append(f"{label} 상회")
            else:
                ma_status.append(f"{label} 하회")
    
    if ma_status:
        result['이동평균선'] = ", ".join(ma_status)
    
    # 5. 스토캐스틱 분석
    stoch_cols = ['STOCH_K', 'STOCH_D']
    if all(col in df.columns for col in stoch_cols):
        k = latest['STOCH_K']
        d = latest['STOCH_D']
        
        # 이전 데이터의 K값 (추세 분석용)
        k_prev = previous['STOCH_K'] if 'STOCH_K' in previous else k
        
        if k > 80 and d > 80:
            result['스토캐스틱'] = f"과매수 구간 (K: {k:.1f}, D: {d:.1f})"
        elif k < 20 and d < 20:
            result['스토캐스틱'] = f"과매도 구간 (K: {k:.1f}, D: {d:.1f})"
        elif k > d and k > k_prev:
            result['스토캐스틱'] = f"상승 반전 가능성 (K: {k:.1f}, D: {d:.1f})"
        elif k < d and k < k_prev:
            result['스토캐스틱'] = f"하락 반전 가능성 (K: {k:.1f}, D: {d:.1f})"
        else:
            result['스토캐스틱'] = f"중립 (K: {k:.1f}, D: {d:.1f})"
    
    return result

def analyze_support_resistance(df: pd.DataFrame) -> Dict[str, List[float]]:
    """
    지지선/저항선 분석
    
    Parameters:
        df (pd.DataFrame): 데이터프레임
        
    Returns:
        Dict[str, List[float]]: 지지선과 저항선 목록
    """
    from src.indicators.support_resistance import find_support_resistance_levels
    
    # 현재가 
    current_price = df['close'].iloc[-1] if 'close' in df.columns else df['Close'].iloc[-1]
    
    # 지지선/저항선 찾기
    support_levels, resistance_levels = find_support_resistance_levels(df)
    
    # 현재 가격과 가까운 수준으로 필터링 및 정렬
    filtered_support = [level for level in support_levels if level < current_price]
    filtered_resistance = [level for level in resistance_levels if level > current_price]
    
    # 가장 가까운 것부터 정렬
    filtered_support = sorted(filtered_support, key=lambda x: current_price - x)
    filtered_resistance = sorted(filtered_resistance, key=lambda x: x - current_price)
    
    # 최대 3개만 선택
    filtered_support = filtered_support[:3]
    filtered_resistance = filtered_resistance[:3]
    
    return {
        'support': filtered_support,
        'resistance': filtered_resistance
    } 