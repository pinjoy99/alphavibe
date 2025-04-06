import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .base_strategy import BaseStrategy
from src.indicators.volatility import bollinger_bands

class BollingerBandsStrategy(BaseStrategy):
    """볼린저 밴드 전략 구현"""
    
    STRATEGY_CODE = "bb"
    STRATEGY_NAME = "볼린저 밴드 전략"
    STRATEGY_DESCRIPTION = "20일 이동평균선을 중심으로 표준편차(2.0)에 따른 밴드를 활용, 하단 밴드 터치 시 매수, 상단 밴드 터치 시 매도"
    
    @classmethod
    def register_strategy_params(cls):
        return [
            {
                "name": "window",
                "type": "int",
                "default": 20,
                "description": "이동평균선 기간",
                "min": 5,
                "max": 100
            },
            {
                "name": "std_dev",
                "type": "float",
                "default": 2.0,
                "description": "표준편차 배수",
                "min": 0.5,
                "max": 4.0
            }
        ]
    
    def __init__(self, window: int = 20, std_dev: float = 2.0):
        """
        Parameters:
            window (int): 이동평균선 기간
            std_dev (float): 표준편차 배수
        """
        self._window = window
        self._std_dev = std_dev
    
    def get_min_required_rows(self) -> int:
        """볼린저 밴드 전략에 필요한 최소 데이터 행 수"""
        return self._window + 5  # 충분한 데이터 보장
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        볼린저 밴드 전략 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 1. 데이터 유효성 검사
        df = self.validate_data(df).copy()
        
        # 2. 볼린저 밴드 계산 - indicators 모듈 사용
        df['upper_band'], df['ma'], df['lower_band'] = bollinger_bands(
            df['close'], window=self._window, num_std=self._std_dev
        )
        
        # 3. 기본 신호 설정
        df['signal'] = 0
        
        # 4. 유효한 데이터에만 신호 적용 (NaN 값 처리)
        valid_idx = df['ma'].notna() & df['upper_band'].notna() & df['lower_band'].notna()
        df.loc[valid_idx & (df['close'] < df['lower_band']), 'signal'] = 1  # 매수 신호 (하단 밴드 아래로)
        df.loc[valid_idx & (df['close'] > df['upper_band']), 'signal'] = -1  # 매도 신호 (상단 밴드 위로)
        
        # 5. 신호 변화 감지
        df['position'] = df['signal'].diff()
        
        # 6. 첫 번째 유효한 신호에 대한 포지션 직접 설정
        first_valid_idx = df[valid_idx].index[0] if not df[valid_idx].empty else None
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
            "std_dev": self._std_dev
        } 