import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy
from .sma_strategy import SMAStrategy

class SMAStopLossStrategy(SMAStrategy):
    """
    SMA 전략에 익절(Take Profit)과 손절(Stop Loss)을 추가한 전략
    """
    
    def __init__(self, short_window: int = 10, long_window: int = 30, 
                 take_profit: float = 0.10, stop_loss: float = 0.03):
        """
        Parameters:
            short_window (int): 단기 이동평균선 기간
            long_window (int): 장기 이동평균선 기간
            take_profit (float): 익절 기준점 (예: 0.10은 10% 수익)
            stop_loss (float): 손절 기준점 (예: 0.03은 3% 손실)
        """
        super().__init__(short_window, long_window)
        self._take_profit = take_profit
        self._stop_loss = stop_loss
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        SMA 전략 적용 후 익절/손절 로직 추가
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 1. 기본 SMA 전략 적용
        df = super().apply(df).copy()
        
        # 2. 추가 컬럼 초기화
        df['entry_price'] = np.nan
        df['position_return'] = 0.0
        df['stop_loss_trigger'] = False
        df['take_profit_trigger'] = False
        
        # 3. 포지션 관리 변수
        current_position = 0  # 0: 포지션 없음, 1: 매수, -1: 매도
        entry_price = 0
        
        # 4. 각 행을 반복하며 익절/손절 적용
        for i in range(len(df)):
            # 이전 포지션 변화 확인
            if df['position'].iloc[i] != 0:
                if df['position'].iloc[i] > 0:  # 매수 신호
                    current_position = 1
                    entry_price = df['close'].iloc[i]
                elif df['position'].iloc[i] < 0:  # 매도 신호
                    current_position = 0
                    entry_price = 0
            
            # 진입 가격 저장
            if current_position != 0:
                df.loc[df.index[i], 'entry_price'] = entry_price
                
                # 현재 수익률 계산
                current_price = df['close'].iloc[i]
                if entry_price > 0:
                    position_return = (current_price - entry_price) / entry_price
                    df.loc[df.index[i], 'position_return'] = position_return
                    
                    # 익절/손절 조건 확인
                    if position_return >= self._take_profit:
                        df.loc[df.index[i], 'take_profit_trigger'] = True
                        df.loc[df.index[i], 'signal'] = -1  # 매도 신호로 변경
                        df.loc[df.index[i], 'position'] = -1 if i == 0 else -current_position
                        current_position = 0
                        entry_price = 0
                    elif position_return <= -self._stop_loss:
                        df.loc[df.index[i], 'stop_loss_trigger'] = True
                        df.loc[df.index[i], 'signal'] = -1  # 매도 신호로 변경
                        df.loc[df.index[i], 'position'] = -1 if i == 0 else -current_position
                        current_position = 0
                        entry_price = 0
        
        return df
    
    @property
    def name(self) -> str:
        """전략 이름"""
        return "SMA_StopLoss"
    
    @property
    def params(self) -> Dict[str, Any]:
        """전략 파라미터"""
        params = super().params
        params.update({
            "take_profit": self._take_profit,
            "stop_loss": self._stop_loss
        })
        return params 