from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List, ClassVar, Optional

class BaseStrategy(ABC):
    """트레이딩 전략의 기본 인터페이스"""
    
    # 전략 메타데이터 (각 서브클래스에서 덮어씀)
    STRATEGY_CODE: ClassVar[str] = ""
    STRATEGY_NAME: ClassVar[str] = ""
    STRATEGY_DESCRIPTION: ClassVar[str] = ""
    
    @classmethod
    def register_strategy_params(cls) -> List[Dict[str, Any]]:
        """
        전략 파라미터 등록 (자동 문서화 및 CLI에서 사용)
        기본적으로 빈 목록 반환
        """
        return []
    
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
    
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        데이터 유효성 검사 및 전처리
        
        Parameters:
            df (pd.DataFrame): 검증할 OHLCV 데이터
            
        Returns:
            pd.DataFrame: 검증된 데이터프레임
            
        Raises:
            ValueError: 데이터가 불충분한 경우
        """
        # 데이터 충분성 검사
        min_required_rows = self.get_min_required_rows()
        if len(df) < min_required_rows:
            raise ValueError(f"전략 적용에 최소 {min_required_rows}개 행이 필요합니다. 현재: {len(df)}")
        return df
    
    def get_min_required_rows(self) -> int:
        """
        전략에 필요한 최소 데이터 행 수 반환
        
        Returns:
            int: 최소 필요 행 수
        """
        return 30  # 기본값, 하위 클래스에서 재정의 필요
    
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