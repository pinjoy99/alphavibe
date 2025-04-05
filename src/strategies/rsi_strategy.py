import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    """RSI(상대강도지수) 전략 구현"""
    
    def __init__(self, window: int = 14, overbought: float = 70.0, oversold: float = 30.0):
        """
        Parameters:
            window (int): RSI 계산을 위한 기간
            overbought (float): 과매수 기준점 (기본값: 70)
            oversold (float): 과매도 기준점 (기본값: 30)
        """
        self._window = window
        self._overbought = overbought
        self._oversold = oversold
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        RSI 전략 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 복사본을 생성하여 원본 데이터 보존
        df = df.copy()
        
        # RSI 계산
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self._window).mean()
        avg_loss = loss.rolling(window=self._window).mean()
        
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 신호 생성
        df['signal'] = 0
        df.loc[df['rsi'] < self._oversold, 'signal'] = 1  # 매수 신호 (RSI가 과매도 지점 아래로)
        df.loc[df['rsi'] > self._overbought, 'signal'] = -1  # 매도 신호 (RSI가 과매수 지점 위로)
        
        # 신호 변화 감지
        df['position'] = df['signal'].diff()
        
        return df
    
    @property
    def name(self) -> str:
        """전략 이름"""
        return "RSI"
    
    @property
    def params(self) -> Dict[str, Any]:
        """전략 파라미터"""
        return {
            "window": self._window,
            "overbought": self._overbought,
            "oversold": self._oversold
        } 