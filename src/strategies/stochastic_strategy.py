import pandas as pd
import numpy as np
from typing import Dict, Any, List, ClassVar
from .base_strategy import BaseStrategy
from src.indicators.momentum import stochastic

class StochasticStrategy(BaseStrategy):
    """
    스토캐스틱 오실레이터 전략
    
    스토캐스틱 오실레이터는 모멘텀 지표로서 현재 가격이 일정 기간의 가격 범위 내에서 
    어디에 위치하는지를 나타냅니다. %K와 %D 라인을 사용하여 과매수/과매도 상태와 
    교차 시그널을 통한 매매 시점을 포착합니다.
    """
    
    # 전략 메타데이터
    STRATEGY_CODE: ClassVar[str] = "stochastic"
    STRATEGY_NAME: ClassVar[str] = "스토캐스틱 오실레이터 전략"
    STRATEGY_DESCRIPTION: ClassVar[str] = "과매수/과매도 상태를 감지하고 %K와 %D 라인의 교차 시점을 활용한 전략"
    
    # 전략 파라미터 레지스트리
    @classmethod
    def register_strategy_params(cls) -> List[Dict[str, Any]]:
        """
        전략 파라미터를 등록합니다.
        """
        return [
            {
                "name": "k_period",
                "type": "int",
                "default": 14,
                "description": "%K 계산 기간",
                "min": 5,
                "max": 30
            },
            {
                "name": "d_period",
                "type": "int",
                "default": 3,
                "description": "%D 계산 기간 (평활화)",
                "min": 1,
                "max": 10
            },
            {
                "name": "slowing",
                "type": "int",
                "default": 3,
                "description": "슬로잉 기간",
                "min": 1,
                "max": 10
            },
            {
                "name": "overbought",
                "type": "int",
                "default": 80,
                "description": "과매수 기준값",
                "min": 50,
                "max": 95
            },
            {
                "name": "oversold",
                "type": "int",
                "default": 20,
                "description": "과매도 기준값",
                "min": 5,
                "max": 50
            }
        ]
    
    def __init__(self, k_period: int = 14, d_period: int = 3, slowing: int = 3, 
                 overbought: int = 80, oversold: int = 20):
        """
        Parameters:
            k_period (int): %K 계산 기간 (일반적으로 14일)
            d_period (int): %D 계산 기간 (일반적으로 3일)
            slowing (int): 슬로잉 기간 (일반적으로 3일)
            overbought (int): 과매수 기준값 (일반적으로 80%)
            oversold (int): 과매도 기준값 (일반적으로 20%)
        """
        self._k_period = k_period
        self._d_period = d_period
        self._slowing = slowing
        self._overbought = overbought
        self._oversold = oversold
    
    def get_min_required_rows(self) -> int:
        """
        전략에 필요한 최소 데이터 행 수 반환
        """
        return self._k_period + self._d_period + self._slowing + 5
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        스토캐스틱 오실레이터 전략 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 1. 데이터 유효성 검사
        df = self.validate_data(df).copy()
        
        # 2. 스토캐스틱 오실레이터 계산
        # 가격 범위에서의 위치 계산 (최근 n일 동안의 최고가/최저가 대비 현재 종가의 위치)
        high_n = df['high'].rolling(window=self._k_period).max()
        low_n = df['low'].rolling(window=self._k_period).min()
        
        # %K 계산 (Fast %K)
        fast_k = 100 * ((df['close'] - low_n) / (high_n - low_n))
        
        # 슬로잉 적용 (Slow %K)
        slow_k = fast_k.rolling(window=self._slowing).mean()
        
        # %D 계산 (Slow %K의 이동평균)
        slow_d = slow_k.rolling(window=self._d_period).mean()
        
        # 데이터프레임에 추가
        df['stoch_k'] = slow_k
        df['stoch_d'] = slow_d
        
        # 3. 신호 생성
        df['signal'] = 0  # 기본값: 중립
        
        # 과매도 상태에서 %K가 %D를 상향 돌파할 때 매수
        buy_signal = (df['stoch_k'] > df['stoch_d']) & (df['stoch_k'].shift(1) <= df['stoch_d'].shift(1)) & (df['stoch_k'] < self._overbought) & (df['stoch_k'] > self._oversold)
        
        # 과매수 상태에서 %K가 %D를 하향 돌파할 때 매도
        sell_signal = (df['stoch_k'] < df['stoch_d']) & (df['stoch_k'].shift(1) >= df['stoch_d'].shift(1)) & (df['stoch_k'] > self._oversold) & (df['stoch_k'] < self._overbought)
        
        # 추가 매수 시그널: 과매도 존에서 반등 시작
        deep_oversold_buy = (df['stoch_k'] > df['stoch_k'].shift(1)) & (df['stoch_k'] < self._oversold) & (df['stoch_k'].shift(1) < self._oversold)
        
        # 신호 적용
        df.loc[buy_signal | deep_oversold_buy, 'signal'] = 1  # 매수
        df.loc[sell_signal, 'signal'] = -1  # 매도
        
        # 4. 신호 변화 감지 (거래 시점 식별)
        df['position'] = df['signal'].diff()
        
        # 5. 첫 번째 유효한 신호에 대한 포지션 설정
        valid_idx = df['signal'].notna()
        first_valid_idxs = df[valid_idx & (df['signal'] != 0)].index
        if len(first_valid_idxs) > 0:
            first_valid_idx = first_valid_idxs[0]
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
            "k_period": self._k_period,
            "d_period": self._d_period,
            "slowing": self._slowing,
            "overbought": self._overbought,
            "oversold": self._oversold
        }
        
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