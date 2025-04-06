import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    """RSI(상대강도지수) 전략 구현"""
    
    STRATEGY_CODE = "rsi"
    STRATEGY_NAME = "RSI 전략"
    STRATEGY_DESCRIPTION = "14일 기준 RSI 지표로 과매수(70)/과매도(30) 상태를 활용, 과매도 상태에서 반등 시 매수, 과매수 상태에서 하락 시 매도"
    
    @classmethod
    def register_strategy_params(cls):
        return [
            {
                "name": "window",
                "type": "int",
                "default": 14,
                "description": "RSI 계산 기간",
                "min": 2,
                "max": 50
            },
            {
                "name": "overbought",
                "type": "float",
                "default": 65.0,
                "description": "과매수 기준점",
                "min": 50.0,
                "max": 90.0
            },
            {
                "name": "oversold",
                "type": "float",
                "default": 35.0,
                "description": "과매도 기준점",
                "min": 10.0,
                "max": 50.0
            },
            {
                "name": "exit_overbought",
                "type": "float",
                "default": 55.0,
                "description": "매도 포지션 종료 기준점",
                "min": 40.0,
                "max": 60.0
            },
            {
                "name": "exit_oversold",
                "type": "float",
                "default": 45.0,
                "description": "매수 포지션 종료 기준점",
                "min": 40.0,
                "max": 60.0
            }
        ]
    
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
    
    def get_min_required_rows(self) -> int:
        """RSI 전략에 필요한 최소 데이터 행 수"""
        return self._window + 10  # RSI 계산 + 충분한 거래 공간
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        RSI 전략 적용 - 개선된 진입/퇴출 전략
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 1. 데이터 유효성 검사
        df = self.validate_data(df).copy()
        
        # 2. RSI 계산
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 지수이동평균 사용 (SMA보다 더 반응이 빠름)
        avg_gain = gain.ewm(com=self._window-1, min_periods=self._window).mean()
        avg_loss = loss.ewm(com=self._window-1, min_periods=self._window).mean()
        
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 3. 신호 초기화
        df['signal'] = 0
        
        # 4. 유효한 데이터 확인
        valid_idx = df['rsi'].notna()
        
        # 5. 포지션 추적 변수 (0: 없음, 1: 매수 포지션)
        position = 0
        
        # 6. 유효한 데이터에만 신호 적용
        valid_rows = df[valid_idx]
        for i in range(len(valid_rows)):
            idx = valid_rows.index[i]
            current_rsi = valid_rows['rsi'].iloc[i]
            
            if position == 0:  # 현재 포지션 없음
                if current_rsi < self._oversold:
                    # 과매도 상태에서 매수 신호
                    df.loc[idx, 'signal'] = 1
                    position = 1
                elif current_rsi > self._overbought:
                    # 과매수 상태에서 매도 신호 (숏 포지션)
                    df.loc[idx, 'signal'] = -1
                    position = -1
            
            elif position == 1:  # 매수 포지션 보유
                if current_rsi > self._exit_oversold:
                    # 매수 포지션 청산
                    df.loc[idx, 'signal'] = -1
                    position = 0
                    
                    # 즉시 과매수 조건 확인
                    if current_rsi > self._overbought:
                        df.loc[idx, 'signal'] = -1
                        position = -1
            
            elif position == -1:  # 매도 포지션 보유 (숏)
                if current_rsi < self._exit_overbought:
                    # 매도 포지션 청산
                    df.loc[idx, 'signal'] = 1
                    position = 0
                    
                    # 즉시 과매도 조건 확인
                    if current_rsi < self._oversold:
                        df.loc[idx, 'signal'] = 1
                        position = 1
        
        # 7. 신호 변화 감지
        df['position'] = df['signal'].diff()
        
        # 8. 첫 번째 유효한 신호에 대한 포지션 직접 설정
        first_valid_signal_idx = df[valid_idx & (df['signal'] != 0)].index[0] if not df[valid_idx & (df['signal'] != 0)].empty else None
        if first_valid_signal_idx is not None:
            df.loc[first_valid_signal_idx, 'position'] = df.loc[first_valid_signal_idx, 'signal']
        
        return df
    
    @property
    def name(self) -> str:
        """전략 이름"""
        return self.STRATEGY_NAME
    
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