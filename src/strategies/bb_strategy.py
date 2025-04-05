import pandas as pd
from typing import Dict, Any
from .base_strategy import BaseStrategy

class BollingerBandsStrategy(BaseStrategy):
    """볼린저 밴드 전략 구현"""
    
    def __init__(self, window: int = 20, std_dev: float = 2.0):
        """
        Parameters:
            window (int): 이동평균선 기간
            std_dev (float): 표준편차 배수
        """
        self._window = window
        self._std_dev = std_dev
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        볼린저 밴드 전략 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 복사본을 생성하여 원본 데이터 보존
        df = df.copy()
        
        # 볼린저 밴드 계산
        df['ma'] = df['close'].rolling(window=self._window).mean()
        df['std'] = df['close'].rolling(window=self._window).std()
        df['upper_band'] = df['ma'] + (df['std'] * self._std_dev)
        df['lower_band'] = df['ma'] - (df['std'] * self._std_dev)
        
        # 신호 생성
        df['signal'] = 0
        df.loc[df['close'] < df['lower_band'], 'signal'] = 1  # 매수 신호 (하단 밴드 아래로)
        df.loc[df['close'] > df['upper_band'], 'signal'] = -1  # 매도 신호 (상단 밴드 위로)
        
        # 신호 변화 감지
        df['position'] = df['signal'].diff()
        
        return df
    
    @property
    def name(self) -> str:
        """전략 이름"""
        return "BB"
    
    @property
    def params(self) -> Dict[str, Any]:
        """전략 파라미터"""
        return {
            "window": self._window,
            "std_dev": self._std_dev
        } 