"""
통합 지표 계산 모듈

다양한 기술적 지표를 통합적으로 계산하는 함수를 제공합니다.
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Union, Tuple

from .moving_averages import calculate_moving_averages
from .momentum import calculate_momentum_indicators
from .volatility import calculate_volatility_indicators
from .trend import calculate_trend_indicators
from .patterns import calculate_price_patterns

def calculate_all_indicators(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    모든 기술적 지표를 통합적으로 계산
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        config (Optional[Dict[str, Any]]): 지표 계산 설정 (기본값: None)
            - moving_averages: 이동평균선 설정
                - ma_types: 이동평균 유형 목록 (예: ['sma', 'ema'])
                - windows: 이동평균 기간 목록 (예: [5, 10, 20, 50, 200])
            - volatility: 변동성 지표 설정
                - bb_window: 볼린저 밴드 기간 (기본값: 20)
                - bb_std_dev: 볼린저 밴드 표준편차 (기본값: 2.0)
                - atr_window: ATR 기간 (기본값: 14)
            - momentum: 모멘텀 지표 설정
                - rsi_window: RSI 기간 (기본값: 14)
                - macd_fast: MACD 단기 기간 (기본값: 12)
                - macd_slow: MACD 장기 기간 (기본값: 26)
                - macd_signal: MACD 신호선 기간 (기본값: 9)
                - stoch_k: 스토캐스틱 %K 기간 (기본값: 14)
                - stoch_d: 스토캐스틱 %D 기간 (기본값: 3)
            - trend: 추세 지표 설정
                - adx_window: ADX 기간 (기본값: 14)
                - aroon_window: Aroon 기간 (기본값: 25)
            - patterns: 가격 패턴 설정
                - sr_window: 지지/저항선 윈도우 (기본값: 10)
                - sr_threshold: 지지/저항선 임계값 (기본값: 0.02)
                - pivot_method: 피봇 포인트 방식 (기본값: 'standard')
    
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: 
            - 지표가 추가된 데이터프레임
            - 계산된 지표의 메타데이터
    """
    # 기본 설정 정의
    default_config = {
        'moving_averages': {
            'ma_types': ['sma', 'ema'],
            'windows': [5, 10, 20, 50, 200]
        },
        'volatility': {
            'bb_window': 20,
            'bb_std_dev': 2.0,
            'atr_window': 14
        },
        'momentum': {
            'rsi_window': 14,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'stoch_k': 14,
            'stoch_d': 3
        },
        'trend': {
            'adx_window': 14,
            'aroon_window': 25
        },
        'patterns': {
            'sr_window': 10,
            'sr_threshold': 0.02,
            'pivot_method': 'standard'
        }
    }
    
    # 사용자 설정으로 기본 설정 업데이트
    if config:
        for category, params in config.items():
            if category in default_config:
                default_config[category].update(params)
    
    # 최종 설정
    config = default_config
    result_df = df.copy()
    metadata = {}
    
    # 1. 이동평균선 계산
    result_df = calculate_moving_averages(
        result_df, 
        ma_types=config['moving_averages']['ma_types'],
        windows=config['moving_averages']['windows']
    )
    
    # 2. 변동성 지표 계산
    result_df = calculate_volatility_indicators(result_df)
    
    # 3. 모멘텀 지표 계산
    result_df = calculate_momentum_indicators(result_df)
    
    # 4. 추세 지표 계산
    result_df = calculate_trend_indicators(result_df)
    
    # 5. 가격 패턴 분석
    result_df = calculate_price_patterns(result_df)
    
    # 메타데이터 수집
    metadata = {
        'support_levels': result_df.attrs.get('support_levels', []),
        'resistance_levels': result_df.attrs.get('resistance_levels', []),
        'fibonacci_levels': result_df.attrs.get('fibonacci_levels', {}),
        'is_uptrend': result_df.attrs.get('is_uptrend', None),
        'config': config
    }
    
    # 차트 시각화에 필요한 중요 지표 컬럼 목록 추가
    metadata['key_indicators'] = {
        'moving_averages': [f"{ma_type}_{window}" for ma_type in config['moving_averages']['ma_types'] 
                           for window in config['moving_averages']['windows']],
        'volatility': ['upper_band', 'middle_band', 'lower_band', 'atr'],
        'momentum': ['rsi', 'macd', 'signal_line', 'macd_hist', 'stoch_k', 'stoch_d'],
        'trend': ['adx', 'plus_di', 'minus_di', 'aroon_up', 'aroon_down']
    }
    
    return result_df, metadata 