import pandas as pd
import numpy as np
from typing import Dict, Any, List, ClassVar
from .base_strategy import BaseStrategy
from src.indicators.moving_averages import sma, calculate_moving_averages

class SMAStrategy(BaseStrategy):
    """단순 이동평균선(SMA) 전략 구현"""
    
    # 전략 메타데이터
    STRATEGY_CODE: ClassVar[str] = "sma"
    STRATEGY_NAME: ClassVar[str] = "이동평균선 전략"
    STRATEGY_DESCRIPTION: ClassVar[str] = "단기/장기 이동평균선의 교차 시점에 매수/매도 신호 발생"
    
    @classmethod
    def register_strategy_params(cls) -> List[Dict[str, Any]]:
        """전략 파라미터 등록"""
        return [
            {
                "name": "short_window",
                "type": "int",
                "default": 10,
                "description": "단기 이동평균선 기간",
                "min": 2,
                "max": 50
            },
            {
                "name": "long_window",
                "type": "int",
                "default": 30,
                "description": "장기 이동평균선 기간",
                "min": 5,
                "max": 200
            }
        ]
    
    def __init__(self, short_window: int = 10, long_window: int = 30):
        """
        Parameters:
            short_window (int): 단기 이동평균선 기간
            long_window (int): 장기 이동평균선 기간
        """
        self._short_window = short_window
        self._long_window = long_window
    
    def get_min_required_rows(self) -> int:
        """SMA 전략에 필요한 최소 데이터 행 수"""
        return self._long_window + 5  # 충분한 데이터 보장
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        단순 이동평균선(SMA) 전략 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 1. 데이터 유효성 검사
        df = self.validate_data(df).copy()
        
        # 2. indicators 모듈을 사용하여 이동평균선 계산
        ma_types = ['sma', 'sma']
        windows = [self._short_window, self._long_window]
        
        # 2.1 calculate_moving_averages 함수 사용
        df = calculate_moving_averages(df, ma_types=ma_types, windows=windows)
        
        # 2.2 단기/장기 이동평균선 컬럼 이름
        short_ma_col = f'sma_{self._short_window}'
        long_ma_col = f'sma_{self._long_window}'
        
        # 2.3 레거시 호환을 위해 'short_ma'와 'long_ma' 컬럼도 추가
        df['short_ma'] = df[short_ma_col]
        df['long_ma'] = df[long_ma_col]
        
        # 3. 기본 신호 설정
        df['signal'] = 0
        
        # 4. 유효한 데이터에만 신호 적용 (NaN 값 처리)
        valid_idx = df[short_ma_col].notna() & df[long_ma_col].notna()
        df.loc[valid_idx & (df[short_ma_col] > df[long_ma_col]), 'signal'] = 1  # 매수 신호
        df.loc[valid_idx & (df[short_ma_col] < df[long_ma_col]), 'signal'] = -1  # 매도 신호
        
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
        return self.STRATEGY_NAME
    
    @property
    def params(self) -> Dict[str, Any]:
        """전략 파라미터"""
        return {
            "short_window": self._short_window,
            "long_window": self._long_window
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