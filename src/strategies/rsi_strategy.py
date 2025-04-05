import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    """RSI(상대강도지수) 전략 구현"""
    
    def __init__(self, window: int = 14, overbought: float = 65.0, oversold: float = 35.0, 
                 exit_overbought: float = 55.0, exit_oversold: float = 45.0):
        """
        Parameters:
            window (int): RSI 계산을 위한 기간
            overbought (float): 과매수 기준점 (기본값: 65)
            oversold (float): 과매도 기준점 (기본값: 35)
            exit_overbought (float): 매도 포지션 종료 기준점 (기본값: 55)
            exit_oversold (float): 매수 포지션 종료 기준점 (기본값: 45)
        """
        self._window = window
        self._overbought = overbought
        self._oversold = oversold
        self._exit_overbought = exit_overbought
        self._exit_oversold = exit_oversold
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        RSI 전략 적용 - 개선된 진입/퇴출 전략
        
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
        
        # 지수이동평균 사용 (SMA보다 더 반응이 빠름)
        avg_gain = gain.ewm(com=self._window-1, min_periods=self._window).mean()
        avg_loss = loss.ewm(com=self._window-1, min_periods=self._window).mean()
        
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 신호 초기화
        df['signal'] = 0
        
        # 포지션 추적 변수 (0: 없음, 1: 매수 포지션)
        position = 0
        
        for i in range(self._window, len(df)):
            current_rsi = df['rsi'].iloc[i]
            
            if position == 0:  # 현재 포지션 없음
                if current_rsi < self._oversold:
                    # 과매도 상태에서 매수 신호
                    df.loc[df.index[i], 'signal'] = 1
                    position = 1
                elif current_rsi > self._overbought:
                    # 과매수 상태에서 매도 신호 (숏 포지션)
                    df.loc[df.index[i], 'signal'] = -1
                    position = -1
            
            elif position == 1:  # 매수 포지션 보유
                if current_rsi > self._exit_oversold:
                    # 매수 포지션 청산
                    df.loc[df.index[i], 'signal'] = -1
                    position = 0
                    
                    # 즉시 과매수 조건 확인
                    if current_rsi > self._overbought:
                        df.loc[df.index[i], 'signal'] = -1
                        position = -1
            
            elif position == -1:  # 매도 포지션 보유 (숏)
                if current_rsi < self._exit_overbought:
                    # 매도 포지션 청산
                    df.loc[df.index[i], 'signal'] = 1
                    position = 0
                    
                    # 즉시 과매도 조건 확인
                    if current_rsi < self._oversold:
                        df.loc[df.index[i], 'signal'] = 1
                        position = 1
        
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
            "oversold": self._oversold,
            "exit_overbought": self._exit_overbought,
            "exit_oversold": self._exit_oversold
        } 