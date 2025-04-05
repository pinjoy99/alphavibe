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
        
        # 2. 볼린저 밴드 계산
        df['ma'] = df['close'].rolling(window=self._window).mean()
        df['std'] = df['close'].rolling(window=self._window).std()
        df['upper_band'] = df['ma'] + (df['std'] * self._std_dev)
        df['lower_band'] = df['ma'] - (df['std'] * self._std_dev)
        
        # 3. 기본 신호 설정
        df['signal'] = 0
        
        # 4. 유효한 데이터에만 신호 적용 (NaN 값 처리)
        valid_idx = df['ma'].notna() & df['std'].notna() & df['upper_band'].notna() & df['lower_band'].notna()
        df.loc[valid_idx & (df['close'] < df['lower_band']), 'signal'] = 1  # 매수 신호 (하단 밴드 아래로)
        df.loc[valid_idx & (df['close'] > df['upper_band']), 'signal'] = -1  # 매도 신호 (상단 밴드 위로)
        
        # 5. 신호 변화 감지
        df['position'] = df['signal'].diff()
        
        # 6. 첫 번째 유효한 신호에 대한 포지션 직접 설정
        first_valid_idx = df[valid_idx].index[0] if not df[valid_idx].empty else None
        if first_valid_idx is not None:
            df.loc[first_valid_idx, 'position'] = df.loc[first_valid_idx, 'signal']
        
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