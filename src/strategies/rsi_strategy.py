import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .base_strategy import BaseStrategy
from src.indicators.momentum import rsi

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
                "default": 70.0,
                "description": "과매수 기준점",
                "min": 50.0,
                "max": 90.0
            },
            {
                "name": "oversold",
                "type": "float",
                "default": 30.0,
                "description": "과매도 기준점",
                "min": 10.0,
                "max": 50.0
            },
            {
                "name": "exit_overbought",
                "type": "float",
                "default": 50.0,
                "description": "매도 포지션 종료 기준점",
                "min": 40.0,
                "max": 60.0
            },
            {
                "name": "exit_oversold",
                "type": "float",
                "default": 50.0,
                "description": "매수 포지션 종료 기준점",
                "min": 40.0,
                "max": 60.0
            },
            {
                "name": "price_check_period",
                "type": "int",
                "default": 7,
                "description": "가격 확인 기간",
                "min": 1,
                "max": 30
            },
            {
                "name": "min_price_drop",
                "type": "float",
                "default": 5.0,
                "description": "최소 가격 하락률 (매수 필터)",
                "min": 0.0,
                "max": 20.0
            },
            {
                "name": "min_price_rise",
                "type": "float",
                "default": 5.0,
                "description": "최소 가격 상승률 (매도 필터)",
                "min": 0.0,
                "max": 20.0
            },
            {
                "name": "min_holding_period",
                "type": "int",
                "default": 3,
                "description": "최소 포지션 유지 기간",
                "min": 0,
                "max": 30
            }
        ]
    
    def __init__(self, window: int = 14, overbought: float = 70.0, oversold: float = 30.0, 
                 exit_overbought: float = 50.0, exit_oversold: float = 50.0,
                 price_check_period: int = 7, min_price_drop: float = 5.0, 
                 min_price_rise: float = 5.0, min_holding_period: int = 3):
        """
        Parameters:
            window (int): RSI 계산을 위한 기간
            overbought (float): 과매수 기준점 (기본값: 70)
            oversold (float): 과매도 기준점 (기본값: 30)
            exit_overbought (float): 매도 포지션 종료 기준점 (기본값: 50)
            exit_oversold (float): 매수 포지션 종료 기준점 (기본값: 50)
            price_check_period (int): 가격 확인 기간 (기본값: 7)
            min_price_drop (float): 최소 가격 하락률 (매수 필터) (기본값: 5.0)
            min_price_rise (float): 최소 가격 상승률 (매도 필터) (기본값: 5.0)
            min_holding_period (int): 최소 포지션 유지 기간 (기본값: 3)
        """
        self._window = window
        self._overbought = overbought
        self._oversold = oversold
        self._exit_overbought = exit_overbought
        self._exit_oversold = exit_oversold
        self._price_check_period = price_check_period
        self._min_price_drop = min_price_drop
        self._min_price_rise = min_price_rise
        self._min_holding_period = min_holding_period
    
    def get_min_required_rows(self) -> int:
        """RSI 전략에 필요한 최소 데이터 행 수"""
        return self._window + 10  # RSI 계산 + 충분한 거래 공간
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        RSI 전략을 데이터프레임에 적용하여 매수/매도 신호를 생성
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 데이터 유효성 검사
        df = self.validate_data(df).copy()
        
        # RSI 계산 - indicators 모듈 사용
        df['rsi'] = rsi(df['close'], window=self._window)
        
        # 유효한 RSI 데이터 확인
        valid_idx = df['rsi'].notna()
        
        # 신호 생성
        df['signal'] = 0
        
        # 과매수/과매도 상태
        df['overbought'] = df['rsi'] > self._overbought
        df['oversold'] = df['rsi'] < self._oversold
        
        # 신호 계산 (개선된 로직)
        for i in range(1, len(df)):
            if not valid_idx.iloc[i] or not valid_idx.iloc[i-1]:
                continue
                
            # 과매도 상태에서 반등 (RSI가 과매도 상태에서 상승세로 전환)
            if df['oversold'].iloc[i-1] and df['rsi'].iloc[i] > df['rsi'].iloc[i-1] and df['rsi'].iloc[i] > self._oversold:
                # 추가 필터: 가격 확인 (낙폭 확인)
                price_drop = (df['close'].iloc[i] / df['close'].iloc[i-self._price_check_period:i].max() - 1) * 100
                if price_drop < 0 and abs(price_drop) >= self._min_price_drop:
                    df.loc[df.index[i], 'signal'] = 1  # 매수 신호
            
            # 과매수 상태에서 하락 (RSI가 과매수 상태에서 하락세로 전환)
            elif df['overbought'].iloc[i-1] and df['rsi'].iloc[i] < df['rsi'].iloc[i-1] and df['rsi'].iloc[i] < self._overbought:
                # 추가 필터: 가격 확인 (상승폭 확인)
                price_rise = (df['close'].iloc[i] / df['close'].iloc[i-self._price_check_period:i].min() - 1) * 100
                if price_rise > 0 and price_rise >= self._min_price_rise:
                    df.loc[df.index[i], 'signal'] = -1  # 매도 신호
        
        # 최소 포지션 유지 기간 적용
        if self._min_holding_period > 0:
            last_trade_idx = -1
            
            for i in range(len(df)):
                if not valid_idx.iloc[i]:
                    continue
                    
                if df['signal'].iloc[i] != 0:  # 신호가 있으면
                    if last_trade_idx >= 0 and (i - last_trade_idx) < self._min_holding_period:
                        # 최소 유지 기간 내에 있으면 신호 무시
                        df.loc[df.index[i], 'signal'] = 0
                    else:
                        # 새로운 거래 기록
                        last_trade_idx = i
        
        # 신호 변화 감지
        df['position'] = df['signal'].diff()
        
        # 첫 번째 유효한 신호에 대한 포지션 직접 설정
        first_valid_idx = df[valid_idx & (df['signal'] != 0)].index[0] if not df[valid_idx & (df['signal'] != 0)].empty else None
        if first_valid_idx is not None:
            df.loc[first_valid_idx, 'position'] = df.loc[first_valid_idx, 'signal']
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        백테스팅을 위한 거래 신호 생성
        
        Parameters:
            df (pd.DataFrame): 이미 apply() 메서드로 지표가 계산된 데이터프레임
            
        Returns:
            pd.DataFrame: 거래 신호가 있는 데이터프레임
        """
        # 신호가 포함된 행만 필터링
        # position 값은 signal의 변화를 나타냄: 1(매수 진입), -1(매도 진입), 0(유지)
        signal_df = df[df['position'] != 0].copy()
        
        # 결과 데이터프레임 준비
        result_df = pd.DataFrame(index=signal_df.index)
        
        # 매수/매도 신호 설정
        result_df['type'] = np.where(signal_df['position'] > 0, 'buy', 'sell')
        result_df['ratio'] = 1.0  # 100% 투자/청산
        
        return result_df
    
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
            "exit_oversold": self._exit_oversold,
            "price_check_period": self._price_check_period,
            "min_price_drop": self._min_price_drop,
            "min_price_rise": self._min_price_rise,
            "min_holding_period": self._min_holding_period
        } 