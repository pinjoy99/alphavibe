from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np
from typing import Dict, Any, List, ClassVar

class SMAStrategyBT(Strategy):
    """Backtesting.py를 사용한 단순 이동평균선(SMA) 전략 구현"""
    
    # 전략 메타데이터
    CODE = "sma"
    NAME = "이동평균선 전략"
    DESCRIPTION = "단기/장기 이동평균선의 교차 시점에 매수/매도 신호 발생"
    
    # 전략 파라미터
    short_window = 10  # 단기 이동평균선 기간
    long_window = 30   # 장기 이동평균선 기간
    
    def init(self):
        """전략 초기화 - 지표 계산"""
        # 데이터 준비
        price = self.data.Close
        
        # 이동평균선 계산 - 백테스팅 내장 함수 사용
        self.sma1 = self.I(lambda: pd.Series(price).rolling(self.short_window).mean())
        self.sma2 = self.I(lambda: pd.Series(price).rolling(self.long_window).mean())
        
        # 신호 저장용 시리즈 생성 (시각화용)
        self.buy_signals = self.I(lambda: np.zeros(len(price)))
        self.sell_signals = self.I(lambda: np.zeros(len(price)))
        
        # 데이터 정보 출력
        print(f"SMA 전략 - 데이터 수: {len(price)}개, 단기MA: {self.short_window}, 장기MA: {self.long_window}")
    
    def next(self):
        """다음 캔들에서의 매매 결정"""
        # 현재 캔들 인덱스
        current_idx = len(self.data) - 1
        
        # 데이터가 충분히 쌓인 후에만 거래
        if current_idx < self.long_window:
            return
            
        # 현재 값 확인 
        price = self.data.Close[-1]
        sma_short = self.sma1[-1]
        sma_long = self.sma2[-1]
        
        # 로그 중요도에 따라 출력 제어
        # print(f"캔들 {current_idx}: 날짜={self.data.index[-1]}, 가격={price:.2f}, 단기MA={sma_short:.2f}, 장기MA={sma_long:.2f}, 차이={(sma_short-sma_long):.2f}")
        
        # backtesting.py의 crossover 함수 사용
        if crossover(self.sma1, self.sma2):
            print(f"✅ 골든 크로스 발생! 날짜={self.data.index[-1]}, 단기MA={sma_short:.2f} > 장기MA={sma_long:.2f}")
            
            # 이전 포지션 종료
            self.position.close()
            
            # 매수
            self.buy()
            self.buy_signals[-1] = 1  # 매수 시그널 표시
            
        # 데드 크로스: 장기선이 단기선 위로 교차
        elif crossover(self.sma2, self.sma1):
            print(f"🔴 데드 크로스 발생! 날짜={self.data.index[-1]}, 단기MA={sma_short:.2f} < 장기MA={sma_long:.2f}")
            
            # 이전 포지션 종료
            self.position.close()
            
            # 매도
            self.sell()
            self.sell_signals[-1] = 1  # 매도 시그널 표시
    
    @classmethod
    def get_parameters(cls) -> Dict[str, Dict[str, Any]]:
        """전략 파라미터 정의"""
        return {
            "short_window": {
                "type": "int",
                "default": 10,
                "description": "단기 이동평균선 기간",
                "min": 2,
                "max": 50
            },
            "long_window": {
                "type": "int",
                "default": 30,
                "description": "장기 이동평균선 기간",
                "min": 5,
                "max": 200
            }
        } 