import pandas as pd
import numpy as np
from typing import Dict, Any, List, ClassVar
from .base_strategy import BaseStrategy

class BuyAndHoldStrategy(BaseStrategy):
    """
    Buy and Hold 전략 - 첫 시점에 매수하여 마지막 시점까지 보유하는 단순 전략
    벤치마크 용도로 사용됩니다.
    """
    
    # 전략 메타데이터
    STRATEGY_CODE: ClassVar[str] = "buyhold"
    STRATEGY_NAME: ClassVar[str] = "Buy & Hold"
    STRATEGY_DESCRIPTION: ClassVar[str] = "첫 시점에 매수하여 마지막 시점까지 보유하는 벤치마크 전략"
    
    @classmethod
    def register_strategy_params(cls) -> List[Dict[str, Any]]:
        """
        전략 파라미터를 등록합니다.
        Buy and Hold 전략은 매개변수가 필요 없습니다.
        
        Returns:
            List[Dict[str, Any]]: 빈 파라미터 목록
        """
        return []
    
    def __init__(self):
        """
        Buy and Hold 전략에는 특별한 초기화 매개변수가 필요하지 않습니다.
        """
        pass
    
    def get_min_required_rows(self) -> int:
        """
        전략에 필요한 최소 데이터 행 수 반환
        Buy and Hold 전략은 최소 2개의 행이 필요합니다 (시작과 끝).
        """
        return 2
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Buy and Hold 전략 로직 적용: 첫 봉에서 매수, 마지막까지 보유
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 데이터 유효성 검사
        df = self.validate_data(df).copy()
        
        # 신호 초기화 (모든 시점에 포지션 없음)
        df['signal'] = 0
        
        # 모든 행에 매수 신호 생성 (전체 기간 동안 매수 포지션 유지)
        if not df.empty:
            # 첫 번째 행에서 매수 신호 생성
            df.loc[df.index[0], 'signal'] = 1
            
            # 두 번째 행부터는 유지 신호(1) 설정
            if len(df) > 1:
                df.loc[df.index[1:], 'signal'] = 1
        
        # 신호 변화 감지 (거래 시점 식별)
        df['position'] = df['signal'].diff()
        
        # 첫 번째 행의 position 설정 (매수 진입점)
        if not df.empty:
            df.loc[df.index[0], 'position'] = df.loc[df.index[0], 'signal']
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        백테스팅을 위한 거래 신호 생성
        
        Parameters:
            df (pd.DataFrame): 이미 apply() 메서드로 지표가 계산된 데이터프레임
            
        Returns:
            pd.DataFrame: 거래 신호가 있는 데이터프레임
        """
        # 기본 구현을 사용하지만, 거래 신호를 명시적으로 반환하기 위해 추가 작업 수행
        result_df = pd.DataFrame(index=df.index)
        
        # 첫 번째 날짜에 매수 신호 생성
        if not df.empty:
            # 매수 신호 데이터프레임 생성
            result_df['type'] = 'buy'
            result_df['ratio'] = 1.0  # 100% 투자
            
            # 첫 번째 행만 유지하고 나머지는 제거
            result_df = result_df.iloc[0:1]
        
        return result_df
    
    @property
    def name(self) -> str:
        """전략 이름"""
        return self.STRATEGY_NAME
    
    @property
    def params(self) -> Dict[str, Any]:
        """전략 파라미터"""
        return {} 