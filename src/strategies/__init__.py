from .base_strategy import BaseStrategy
from .sma_strategy import SMAStrategy
from .bb_strategy import BollingerBandsStrategy
from .macd_strategy import MACDStrategy
from .rsi_strategy import RSIStrategy
from .sma_stoploss_strategy import SMAStopLossStrategy
from .doomsday_cross_strategy import DoomsdayCrossStrategy
from .strategy_registry import StrategyRegistry

# 전략 생성 함수
def create_strategy(strategy_code, **kwargs):
    """
    전략 코드를 기반으로 전략 객체 생성
    
    Parameters:
        strategy_code (str): 전략 코드
        **kwargs: 전략 파라미터
        
    Returns:
        BaseStrategy: 전략 객체 또는 None (일치하는 전략이 없는 경우)
    """
    # 레지스트리를 통해 전략 찾기
    strategy = StrategyRegistry.create_strategy(strategy_code, **kwargs)
    return strategy

__all__ = [
    'BaseStrategy',
    'SMAStrategy',
    'BollingerBandsStrategy',
    'MACDStrategy',
    'RSIStrategy',
    'SMAStopLossStrategy',
    'DoomsdayCrossStrategy',
    'StrategyRegistry',
    'create_strategy'
]
