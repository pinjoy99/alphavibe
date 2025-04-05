from typing import Optional, Dict, Any
from .base_strategy import BaseStrategy
from .sma_strategy import SMAStrategy
from .bb_strategy import BollingerBandsStrategy
from .macd_strategy import MACDStrategy
from .rsi_strategy import RSIStrategy

def create_strategy(strategy_name: str, **kwargs) -> Optional[BaseStrategy]:
    """
    전략 이름에 따라 적절한 전략 객체 생성
    
    Parameters:
        strategy_name (str): 전략 이름 ('sma', 'bb', 'macd', 'rsi')
        **kwargs: 전략별 파라미터
        
    Returns:
        Optional[BaseStrategy]: 전략 객체 또는 None (일치하는 전략이 없는 경우)
    """
    strategies = {
        "sma": SMAStrategy,
        "bb": BollingerBandsStrategy,
        "macd": MACDStrategy,
        "rsi": RSIStrategy
    }
    
    strategy_class = strategies.get(strategy_name.lower())
    if not strategy_class:
        return None
    
    # 전략별 필요한 파라미터만 필터링
    if strategy_name.lower() == "sma":
        filtered_params = {
            k: v for k, v in kwargs.items() 
            if k in ["short_window", "long_window"]
        }
    elif strategy_name.lower() == "bb":
        filtered_params = {
            k: v for k, v in kwargs.items() 
            if k in ["window", "std_dev"]
        }
    elif strategy_name.lower() == "macd":
        filtered_params = {
            k: v for k, v in kwargs.items() 
            if k in ["short_window", "long_window", "signal_window"]
        }
    elif strategy_name.lower() == "rsi":
        filtered_params = {
            k: v for k, v in kwargs.items() 
            if k in ["window", "overbought", "oversold"]
        }
    else:
        filtered_params = {}
    
    return strategy_class(**filtered_params) 