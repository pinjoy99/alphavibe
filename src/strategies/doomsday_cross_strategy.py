import pandas as pd
import numpy as np
from typing import Dict, Any, List, ClassVar
from .base_strategy import BaseStrategy

class DoomsdayCrossStrategy(BaseStrategy):
    """
    둠스데이 크로스 전략 - 50일선과 200일선을 활용한 장기 매매 전략
    
    데드 크로스(50일선이 200일선을 하향 돌파)가 발생하면 강한 매도 신호 생성
    골든 크로스(50일선이 200일선을 상향 돌파)가 발생하면 매수 신호 생성
    
    이 전략은 장기 추세 변화를 감지하는데 효과적이지만
    신호가 발생하는 빈도는 낮은 편입니다.
    """
    
    # 전략 메타데이터
    STRATEGY_CODE: ClassVar[str] = "doomsday"
    STRATEGY_NAME: ClassVar[str] = "둠스데이 크로스 전략"
    STRATEGY_DESCRIPTION: ClassVar[str] = "50일선과 200일선의 크로스를 이용한 장기 매매 전략"
    
    # 전략 파라미터 레지스트리
    @classmethod
    def register_strategy_params(cls) -> List[Dict[str, Any]]:
        """전략 파라미터 등록"""
        return [
            {
                "name": "mid_window",
                "type": "int",
                "default": 50,
                "description": "중기 이동평균선 기간 (일반적으로 50일)",
                "min": 20,
                "max": 100
            },
            {
                "name": "long_window",
                "type": "int",
                "default": 200,
                "description": "장기 이동평균선 기간 (일반적으로 200일)",
                "min": 100,
                "max": 500
            },
            {
                "name": "sell_strength",
                "type": "float",
                "default": 1.0,
                "description": "매도 신호 강도 (1.0-3.0)",
                "min": 1.0,
                "max": 3.0
            }
        ]
    
    def __init__(self, mid_window: int = 50, long_window: int = 200, sell_strength: float = 1.0):
        """
        Parameters:
            mid_window (int): 중기 이동평균선 기간 (일반적으로 50일)
            long_window (int): 장기 이동평균선 기간 (일반적으로 200일)
            sell_strength (float): 매도 신호 강도 (1.0-3.0)
        """
        self._mid_window = mid_window
        self._long_window = long_window
        self._sell_strength = max(1.0, min(3.0, sell_strength))  # 1.0-3.0 범위로 제한
    
    def get_min_required_rows(self) -> int:
        """전략에 필요한 최소 데이터 행 수"""
        return self._long_window + 20  # 충분한 데이터 보장
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        둠스데이 크로스 전략 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 1. 데이터 유효성 검사
        df = self.validate_data(df).copy()
        
        # 2. 이동평균선 계산
        df['mid_ma'] = df['close'].rolling(window=self._mid_window).mean()
        df['long_ma'] = df['close'].rolling(window=self._long_window).mean()
        
        # 3. 기본 신호 설정
        df['signal'] = 0
        
        # 4. 크로스 감지를 위한 헬퍼 컬럼 추가
        df['mid_above_long'] = (df['mid_ma'] > df['long_ma']).astype(int)
        df['cross'] = df['mid_above_long'].diff()  # 1: 상향 돌파, -1: 하향 돌파
        
        # 5. 유효한 데이터에만 신호 적용
        valid_idx = df['mid_ma'].notna() & df['long_ma'].notna()
        
        # 골든 크로스: 50일선이 200일선 상향 돌파 (매수 신호)
        golden_cross_idx = valid_idx & (df['cross'] == 1)
        df.loc[golden_cross_idx, 'signal'] = 1
        
        # 데드 크로스: 50일선이 200일선 하향 돌파 (매도 신호, 강도 적용)
        dead_cross_idx = valid_idx & (df['cross'] == -1)
        df.loc[dead_cross_idx, 'signal'] = -1 * self._sell_strength
        
        # 6. 신호 변화 감지 (거래 시점 식별)
        df['position'] = df['signal'].diff()
        
        # 7. 첫 번째 유효한 신호에 대한 포지션 설정
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
            "mid_window": self._mid_window,
            "long_window": self._long_window,
            "sell_strength": self._sell_strength
        } 