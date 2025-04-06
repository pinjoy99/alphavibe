import pandas as pd
import numpy as np
from typing import Dict, Any, List, ClassVar
from .base_strategy import BaseStrategy

class TemplateStrategy(BaseStrategy):
    """
    템플릿 전략 - 새 전략 개발 시 이 파일을 복사하여 사용하세요
    
    사용 방법:
    1. 이 파일을 복사하여 your_strategy_name_strategy.py 형식으로 저장
    2. 클래스 이름과 내용 수정
    3. register_strategy_params에 파라미터 정보 추가
    4. apply 메서드 구현
    """
    
    # 전략 메타데이터 (코드 구조 개선 부분)
    STRATEGY_CODE: ClassVar[str] = "template"  # 이 부분 수정 (예: "sma_stoploss")
    STRATEGY_NAME: ClassVar[str] = "템플릿 전략"  # 이 부분 수정 (예: "SMA+손익절 전략")
    STRATEGY_DESCRIPTION: ClassVar[str] = "새 전략 개발을 위한 템플릿"  # 이 부분 수정
    
    # 전략 파라미터 레지스트리 (자동 등록을 위한 클래스 메서드)
    @classmethod
    def register_strategy_params(cls) -> List[Dict[str, Any]]:
        """
        전략 파라미터를 등록합니다.
        이 메서드는 자동으로 UI와 CLI에서 파라미터를 인식하는 데 사용됩니다.
        
        Returns:
            List[Dict[str, Any]]: 파라미터 정보 목록
        """
        return [
            {
                "name": "param1",  # 파라미터 이름 (예: "short_window")
                "type": "int",     # 파라미터 타입 (int, float, bool)
                "default": 10,     # 기본값
                "description": "파라미터 1 설명",  # 설명
                "min": 1,          # 최소값 (선택)
                "max": 100         # 최대값 (선택)
            },
            # 추가 파라미터 여기에 정의
        ]
    
    def __init__(self, param1: int = 10):
        """
        Parameters:
            param1 (int): 파라미터 1 설명
        """
        self._param1 = param1
        # 추가 초기화 코드
    
    def get_min_required_rows(self) -> int:
        """
        전략에 필요한 최소 데이터 행 수 반환
        """
        return self._param1 + 10  # 적절히 수정
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        전략 로직 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 1. 데이터 유효성 검사
        df = self.validate_data(df).copy()
        
        # 2. 지표 계산
        # TODO: 여기에 전략 고유의 지표 계산 코드 추가
        
        # 3. 신호 생성
        df['signal'] = 0  # 0: 포지션 없음, 1: 매수, -1: 매도
        
        # TODO: 여기에 매수/매도 신호 생성 로직 구현
        
        # 4. 신호 변화 감지 (거래 시점 식별)
        df['position'] = df['signal'].diff()
        
        # 5. 첫 번째 유효한 신호에 대한 포지션 설정
        valid_idx = df['signal'].notna()
        first_valid_idx = df[valid_idx & (df['signal'] != 0)].index[0] if not df[valid_idx & (df['signal'] != 0)].empty else None
        if first_valid_idx is not None:
            df.loc[first_valid_idx, 'position'] = df.loc[first_valid_idx, 'signal']
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        백테스팅을 위한 거래 신호 생성
        
        이 메서드는 백테스팅 엔진에서 사용되며, apply() 메서드가 계산한 
        signal과 position을 기반으로 실제 거래 신호를 생성합니다.
        
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
        
        # 추가 정보를 포함하는 경우 (선택적)
        # result_df['price'] = signal_df['close']      # 특정 가격으로 매매
        # result_df['amount'] = 특정금액               # 특정 금액만 투자/청산
        # result_df['ratio'] = 특정비율(0.0~1.0)      # 특정 비율만 투자/청산
        
        return result_df
    
    @property
    def name(self) -> str:
        """전략 이름"""
        return self.STRATEGY_NAME
    
    @property
    def params(self) -> Dict[str, Any]:
        """전략 파라미터"""
        return {
            "param1": self._param1,
            # 추가 파라미터
        } 