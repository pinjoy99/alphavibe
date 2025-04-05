from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseStrategy(ABC):
    """트레이딩 전략의 기본 인터페이스"""
    
    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        전략 로직을 적용하고 신호를 생성
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """전략 이름"""
        pass
    
    @property
    @abstractmethod
    def params(self) -> Dict[str, Any]:
        """전략 파라미터"""
        pass 