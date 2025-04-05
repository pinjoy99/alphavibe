import pandas as pd
from typing import Dict, Any
from .base_strategy import BaseStrategy

class MACDStrategy(BaseStrategy):
    """MACD(이동평균수렴확산지수) 전략 구현"""
    
    def __init__(self, short_window: int = 12, long_window: int = 26, signal_window: int = 9):
        """
        Parameters:
            short_window (int): 단기 EMA 기간
            long_window (int): 장기 EMA 기간
            signal_window (int): 시그널 EMA 기간
        """
        self._short_window = short_window
        self._long_window = long_window
        self._signal_window = signal_window
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        MACD 전략 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 복사본을 생성하여 원본 데이터 보존
        df = df.copy()
        
        # MACD 계산
        df['short_ema'] = df['close'].ewm(span=self._short_window, adjust=False).mean()
        df['long_ema'] = df['close'].ewm(span=self._long_window, adjust=False).mean()
        df['macd'] = df['short_ema'] - df['long_ema']
        df['signal_line'] = df['macd'].ewm(span=self._signal_window, adjust=False).mean()
        df['histogram'] = df['macd'] - df['signal_line']
        
        # 신호 생성
        df['signal'] = 0
        df.loc[df['macd'] > df['signal_line'], 'signal'] = 1  # 매수 신호
        df.loc[df['macd'] < df['signal_line'], 'signal'] = -1  # 매도 신호
        
        # 신호 변화 감지
        df['position'] = df['signal'].diff()
        
        return df
    
    @property
    def name(self) -> str:
        """전략 이름"""
        return "MACD"
    
    @property
    def params(self) -> Dict[str, Any]:
        """전략 파라미터"""
        return {
            "short_window": self._short_window,
            "long_window": self._long_window,
            "signal_window": self._signal_window
        } 