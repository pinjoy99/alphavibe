import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy
from src.indicators.momentum import macd

class MACDStrategy(BaseStrategy):
    """MACD(이동평균수렴확산지수) 전략 구현"""
    
    STRATEGY_CODE = "macd"
    STRATEGY_NAME = "MACD 전략"
    STRATEGY_DESCRIPTION = "단기(12일)와 장기(26일) 지수이동평균의 차이와 신호선(9일)을 활용, MACD선이 신호선을 상향 돌파 시 매수, 하향 돌파 시 매도"
    
    @classmethod
    def register_strategy_params(cls):
        return [
            {
                "name": "short_window",
                "type": "int",
                "default": 12,
                "description": "단기 이동평균 기간",
                "min": 2,
                "max": 50
            },
            {
                "name": "long_window",
                "type": "int",
                "default": 26,
                "description": "장기 이동평균 기간",
                "min": 3,
                "max": 100
            },
            {
                "name": "signal_window",
                "type": "int",
                "default": 9,
                "description": "신호선 기간",
                "min": 2,
                "max": 50
            },
            {
                "name": "min_crossover_threshold",
                "type": "float",
                "default": 0.02,
                "description": "최소 크로스오버 임계값",
                "min": 0.0,
                "max": 0.5
            },
            {
                "name": "min_holding_period",
                "type": "int",
                "default": 2,
                "description": "최소 포지션 유지 기간",
                "min": 0,
                "max": 30
            }
        ]
    
    def __init__(self, short_window: int = 12, long_window: int = 26, signal_window: int = 9, 
                 min_crossover_threshold: float = 0.02, min_holding_period: int = 2):
        """
        Parameters:
            short_window (int): 단기 이동평균 기간 (기본값: 12)
            long_window (int): 장기 이동평균 기간 (기본값: 26)
            signal_window (int): 신호선 기간 (기본값: 9)
            min_crossover_threshold (float): 최소 크로스오버 임계값 (기본값: 0.02)
            min_holding_period (int): 최소 포지션 유지 기간 (기본값: 2)
        """
        self._short_window = short_window
        self._long_window = long_window
        self._signal_window = signal_window
        self._min_crossover_threshold = min_crossover_threshold
        self._min_holding_period = min_holding_period
    
    def get_min_required_rows(self) -> int:
        """MACD 전략에 필요한 최소 데이터 행 수"""
        return max(self._long_window, self._short_window) + self._signal_window + 5
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        MACD 전략 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 1. 데이터 유효성 검사
        df = self.validate_data(df).copy()
        
        # 2. MACD 계산 - indicators 모듈 사용
        df['macd'], df['signal_line'], df['histogram'] = macd(
            df['close'], 
            fast_period=self._short_window, 
            slow_period=self._long_window, 
            signal_period=self._signal_window
        )
        
        # 2.1 legacy 호환을 위한 추가 (필요 시)
        df['short_ema'] = df['close'].ewm(span=self._short_window, adjust=False).mean()
        df['long_ema'] = df['close'].ewm(span=self._long_window, adjust=False).mean()
        
        # 3. 유효한 데이터 확인
        valid_idx = (
            df['macd'].notna() & 
            df['signal_line'].notna() & 
            df['histogram'].notna()
        )
        
        # 4. 신호 생성 (기본 로직)
        df['raw_signal'] = 0
        df.loc[valid_idx & (df['macd'] > df['signal_line']), 'raw_signal'] = 1  # 매수 신호
        df.loc[valid_idx & (df['macd'] < df['signal_line']), 'raw_signal'] = -1  # 매도 신호
        
        # 5. 크로스오버 강도 계산
        df['crossover_strength'] = 0.0
        valid_macd_idx = valid_idx & (df['macd'] != 0)
        df.loc[valid_macd_idx, 'crossover_strength'] = np.abs(
            df.loc[valid_macd_idx, 'macd'] - df.loc[valid_macd_idx, 'signal_line']
        ) / np.abs(df.loc[valid_macd_idx, 'macd'])
        
        # 6. 필터링된 신호 생성
        df['signal'] = 0
        
        # 7. 임계값 이상의 크로스오버에만 신호 생성 (유효한 데이터만)
        for i in range(len(df)):
            if not valid_idx.iloc[i]:
                continue
                
            if df['raw_signal'].iloc[i] == 1 and df['crossover_strength'].iloc[i] > self._min_crossover_threshold:
                df.loc[df.index[i], 'signal'] = 1
            elif df['raw_signal'].iloc[i] == -1 and df['crossover_strength'].iloc[i] > self._min_crossover_threshold:
                df.loc[df.index[i], 'signal'] = -1
        
        # 8. 최소 포지션 유지 기간 적용
        if self._min_holding_period > 0:
            last_trade_idx = -1
            last_trade_type = 0
            
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
                        last_trade_type = df['signal'].iloc[i]
        
        # 9. 신호 변화 감지
        df['position'] = df['signal'].diff()
        
        # 10. 첫 번째 유효한 신호에 대한 포지션 직접 설정
        first_valid_idx = df[valid_idx & (df['signal'] != 0)].index[0] if not df[valid_idx & (df['signal'] != 0)].empty else None
        if first_valid_idx is not None:
            df.loc[first_valid_idx, 'position'] = df.loc[first_valid_idx, 'signal']
        
        return df
    
    @property
    def name(self) -> str:
        """전략 이름"""
        return self.STRATEGY_NAME
    
    @property
    def params(self) -> Dict[str, Any]:
        """전략 파라미터"""
        return {
            "short_window": self._short_window,
            "long_window": self._long_window,
            "signal_window": self._signal_window,
            "min_crossover_threshold": self._min_crossover_threshold,
            "min_holding_period": self._min_holding_period
        } 