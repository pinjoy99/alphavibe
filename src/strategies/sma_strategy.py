import pandas as pd
from typing import Dict, Any
from .base_strategy import BaseStrategy

class SMAStrategy(BaseStrategy):
    """단순 이동평균선(SMA) 전략 구현"""
    
    def __init__(self, short_window: int = 10, long_window: int = 30):
        """
        Parameters:
            short_window (int): 단기 이동평균선 기간
            long_window (int): 장기 이동평균선 기간
        """
        self._short_window = short_window
        self._long_window = long_window
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        단순 이동평균선(SMA) 전략 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 복사본을 생성하여 원본 데이터 보존
        df = df.copy()
        
        # 단기/장기 이동평균선 계산
        df['short_ma'] = df['close'].rolling(window=self._short_window).mean()
        df['long_ma'] = df['close'].rolling(window=self._long_window).mean()
        
        # 신호 생성
        df['signal'] = 0
        df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1  # 매수 신호
        df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1  # 매도 신호
        
        # 신호 변화 감지
        df['position'] = df['signal'].diff()
        
        return df
    
    @property
    def name(self) -> str:
        """전략 이름"""
        return "SMA"
    
    @property
    def params(self) -> Dict[str, Any]:
        """전략 파라미터"""
        return {
            "short_window": self._short_window,
            "long_window": self._long_window
        } 