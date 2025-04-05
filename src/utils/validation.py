"""
입력값 검증 관련 유틸리티 함수 모듈
"""
import re
from typing import Any, List, Optional, Tuple, Union

def validate_ticker(ticker: str) -> bool:
    """
    종목 심볼 형식 검증
    
    Parameters:
        ticker (str): 종목 심볼 (예: "KRW-BTC", "BTC")
        
    Returns:
        bool: 유효한 형식이면 True, 아니면 False
    """
    # Upbit 형식: "KRW-BTC", "BTC-ETH" 등
    pattern = r'^[A-Z]{3,4}-[A-Z]{3,4}$|^[A-Z]{3,4}$'
    return bool(re.match(pattern, ticker))

def validate_timeframe(timeframe: str) -> bool:
    """
    시간 프레임 형식 검증
    
    Parameters:
        timeframe (str): 시간 프레임 문자열
        
    Returns:
        bool: 유효한 형식이면 True, 아니면 False
    """
    valid_timeframes = [
        'minute1', 'minute3', 'minute5', 'minute10', 'minute15', 
        'minute30', 'minute60', 'minute240', 'day', 'week', 'month'
    ]
    return timeframe in valid_timeframes

def validate_strategy_params(strategy_type: str, params: dict) -> Tuple[bool, Optional[str]]:
    """
    전략 파라미터 검증
    
    Parameters:
        strategy_type (str): 전략 유형
        params (dict): 검증할 파라미터
        
    Returns:
        Tuple[bool, Optional[str]]: (유효성 여부, 오류 메시지)
    """
    strategy_type = strategy_type.lower()
    
    if strategy_type == 'sma':
        if 'short_window' not in params or 'long_window' not in params:
            return False, "SMA 전략에는 short_window와 long_window 파라미터가 필요합니다."
        if params['short_window'] >= params['long_window']:
            return False, "short_window는 long_window보다 작아야 합니다."
    
    elif strategy_type == 'bb':
        if 'window' not in params or 'std_dev' not in params:
            return False, "볼린저 밴드 전략에는 window와 std_dev 파라미터가 필요합니다."
    
    elif strategy_type == 'macd':
        if 'short_window' not in params or 'long_window' not in params or 'signal_window' not in params:
            return False, "MACD 전략에는 short_window, long_window, signal_window 파라미터가 필요합니다."
    
    elif strategy_type == 'rsi':
        if 'window' not in params or 'overbought' not in params or 'oversold' not in params:
            return False, "RSI 전략에는 window, overbought, oversold 파라미터가 필요합니다."
        if params['oversold'] >= params['overbought']:
            return False, "oversold는 overbought보다 작아야 합니다."
    
    else:
        return False, f"지원되지 않는 전략 유형입니다: {strategy_type}"
    
    return True, None

def validate_period_str(period_str: str) -> bool:
    """
    기간 문자열 검증
    
    Parameters:
        period_str (str): 기간 문자열 (예: 1d, 3d, 1w, 1m, 3m, 6m, 1y)
        
    Returns:
        bool: 유효한 형식이면 True, 아니면 False
    """
    pattern = r'^\d+[dwmy]$'
    return bool(re.match(pattern, period_str)) 