from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np
from typing import Dict, Any

class MACDStrategyBT(Strategy):
    """Backtesting.py를 사용한 MACD 전략 구현"""
    
    # 전략 메타데이터
    CODE = "macd"
    NAME = "MACD 전략"
    DESCRIPTION = "MACD 라인과 시그널 라인의 교차 시점에 매수/매도 신호 발생"
    
    # 전략 파라미터
    fast_period = 12    # 단기 EMA 기간
    slow_period = 26    # 장기 EMA 기간
    signal_period = 9   # 시그널 라인 기간
    
    def init(self):
        """전략 초기화 - 지표 계산"""
        # 데이터 준비
        price = self.data.Close
        
        # MACD 계산
        fast_ema = self.I(lambda: pd.Series(price).ewm(span=self.fast_period, adjust=False).mean())
        slow_ema = self.I(lambda: pd.Series(price).ewm(span=self.slow_period, adjust=False).mean())
        self.macd_line = self.I(lambda: fast_ema - slow_ema)
        
        # 시그널 라인 = MACD의 EMA
        self.signal_line = self.I(lambda: pd.Series(self.macd_line).ewm(span=self.signal_period, adjust=False).mean())
        
        # 히스토그램 = MACD 라인 - 시그널 라인
        self.histogram = self.I(lambda: self.macd_line - self.signal_line)
        
        # 신호 저장용 시리즈 생성 (시각화용)
        self.buy_signals = self.I(lambda: np.zeros(len(price)))
        self.sell_signals = self.I(lambda: np.zeros(len(price)))
        
        # 데이터 정보 출력
        print(f"MACD 전략 - 데이터 수: {len(price)}개, 빠른기간: {self.fast_period}, 느린기간: {self.slow_period}, 시그널기간: {self.signal_period}")
    
    def next(self):
        """다음 캔들에서의 매매 결정"""
        # 현재 캔들 인덱스
        current_idx = len(self.data) - 1
        
        # 데이터가 충분히 쌓인 후에만 거래
        min_period = max(self.slow_period, self.signal_period) + self.fast_period
        if current_idx < min_period:
            return
            
        # 현재 값 확인 
        price = self.data.Close[-1]
        macd = self.macd_line[-1]
        signal = self.signal_line[-1]
        
        # backtesting.py의 crossover 함수 사용
        if crossover(self.macd_line, self.signal_line):
            print(f"✅ 매수 신호 발생! 날짜={self.data.index[-1]}, MACD={macd:.4f} > 시그널={signal:.4f}")
            
            # 이전 포지션 종료
            self.position.close()
            
            # 매수
            self.buy()
            self.buy_signals[-1] = 1  # 매수 시그널 표시
            
        # 매도 신호: 시그널 라인이 MACD 라인 위로 교차
        elif crossover(self.signal_line, self.macd_line):
            print(f"🔴 매도 신호 발생! 날짜={self.data.index[-1]}, MACD={macd:.4f} < 시그널={signal:.4f}")
            
            # 이전 포지션 종료
            self.position.close()
            
            # 매도
            self.sell()
            self.sell_signals[-1] = 1  # 매도 시그널 표시
    
    @classmethod
    def get_parameters(cls) -> Dict[str, Dict[str, Any]]:
        """전략 파라미터 정의"""
        return {
            "fast_period": {
                "type": "int",
                "default": 12,
                "description": "단기 EMA 기간",
                "min": 3,
                "max": 40
            },
            "slow_period": {
                "type": "int",
                "default": 26,
                "description": "장기 EMA 기간",
                "min": 10,
                "max": 50
            },
            "signal_period": {
                "type": "int",
                "default": 9,
                "description": "시그널 라인 기간",
                "min": 3,
                "max": 20
            }
        } 
 