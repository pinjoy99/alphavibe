import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .base_strategy import BaseStrategy
from src.indicators.momentum import macd

class MACDStrategy(BaseStrategy):
    """MACD(이동평균수렴확산지수) 전략 구현"""
    
    STRATEGY_CODE = "macd"
    STRATEGY_NAME = "MACD 전략"
    STRATEGY_DESCRIPTION = "단기(12일)와 장기(26일) 지수이동평균의 차이와 신호선(9일)을 활용, MACD선이 신호선을 상향 돌파 시 매수, 하향 돌파 시 매도"
    
    @classmethod
    def register_strategy_params(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "short_window",
                "type": "int",
                "default": 12,
                "description": "단기 이동평균 기간",
                "min": 2,
                "max": 50
            },
            {
                "name": "long_window",
                "type": "int",
                "default": 26,
                "description": "장기 이동평균 기간",
                "min": 3,
                "max": 100
            },
            {
                "name": "signal_window",
                "type": "int",
                "default": 9,
                "description": "신호선 기간",
                "min": 2,
                "max": 50
            },
            {
                "name": "min_crossover_threshold",
                "type": "float",
                "default": 0.10,
                "description": "최소 크로스오버 임계값",
                "min": 0.0,
                "max": 0.5
            },
            {
                "name": "min_holding_period",
                "type": "int",
                "default": 10,
                "description": "최소 포지션 유지 기간",
                "min": 0,
                "max": 30
            },
            {
                "name": "trend_confirmation_period",
                "type": "int",
                "default": 3,
                "description": "추세 확인 기간 (신호 확정 전 확인 일수)",
                "min": 1,
                "max": 10
            },
            {
                "name": "min_histogram_value",
                "type": "float",
                "default": 0.01,
                "description": "최소 히스토그램 값 (가격 대비 %)",
                "min": 0.0,
                "max": 1.0
            },
            {
                "name": "ma_trend_period",
                "type": "int",
                "default": 50,
                "description": "추세 확인용 이동평균 기간",
                "min": 10,
                "max": 200
            }
        ]
    
    def __init__(self, short_window: int = 12, long_window: int = 26, signal_window: int = 9, 
                 min_crossover_threshold: float = 0.10, min_holding_period: int = 10,
                 trend_confirmation_period: int = 3, min_histogram_value: float = 0.01,
                 ma_trend_period: int = 50):
        """
        Parameters:
            short_window (int): 단기 이동평균 기간 (기본값: 12)
            long_window (int): 장기 이동평균 기간 (기본값: 26)
            signal_window (int): 신호선 기간 (기본값: 9)
            min_crossover_threshold (float): 최소 크로스오버 임계값 (기본값: 0.10)
            min_holding_period (int): 최소 포지션 유지 기간 (기본값: 10)
            trend_confirmation_period (int): 추세 확인 기간 (기본값: 3)
            min_histogram_value (float): 최소 히스토그램 값 (기본값: 0.01)
            ma_trend_period (int): 추세 확인용 이동평균 기간 (기본값: 50)
        """
        self._short_window = short_window
        self._long_window = long_window
        self._signal_window = signal_window
        self._min_crossover_threshold = min_crossover_threshold
        self._min_holding_period = min_holding_period
        self._trend_confirmation_period = trend_confirmation_period
        self._min_histogram_value = min_histogram_value
        self._ma_trend_period = ma_trend_period
    
    def get_min_required_rows(self) -> int:
        """MACD 전략에 필요한 최소 데이터 행 수"""
        return max(self._long_window, self._short_window, self._ma_trend_period) + self._signal_window + self._trend_confirmation_period + 5
    
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        MACD 전략 적용
        
        Parameters:
            df (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 신호가 추가된 데이터프레임
        """
        # 1. 데이터 유효성 검사
        df = self.validate_data(df).copy()
        
        # 2. MACD 계산 - indicators 모듈 사용
        df['macd'], df['signal_line'], df['histogram'] = macd(
            df['close'], 
            fast_period=self._short_window, 
            slow_period=self._long_window, 
            signal_period=self._signal_window
        )
        
        # 2.1 추세 확인용 이동평균 추가
        df['ma_trend'] = df['close'].rolling(window=self._ma_trend_period).mean()
        
        # 2.2 legacy 호환을 위한 추가 (필요 시)
        df['short_ema'] = df['close'].ewm(span=self._short_window, adjust=False).mean()
        df['long_ema'] = df['close'].ewm(span=self._long_window, adjust=False).mean()
        
        # 3. 유효한 데이터 확인
        valid_idx = (
            df['macd'].notna() & 
            df['signal_line'].notna() & 
            df['histogram'].notna() &
            df['ma_trend'].notna()
        )
        
        # 4. 신호 생성 (기본 로직)
        df['raw_signal'] = 0
        df.loc[valid_idx & (df['macd'] > df['signal_line']), 'raw_signal'] = 1  # 매수 신호
        df.loc[valid_idx & (df['macd'] < df['signal_line']), 'raw_signal'] = -1  # 매도 신호
        
        # 5. 크로스오버 강도 계산
        df['crossover_strength'] = 0.0
        valid_macd_idx = valid_idx & (df['macd'] != 0)
        df.loc[valid_macd_idx, 'crossover_strength'] = np.abs(
            df.loc[valid_macd_idx, 'macd'] - df.loc[valid_macd_idx, 'signal_line']
        ) / np.abs(df.loc[valid_macd_idx, 'macd'])
        
        # 6. 히스토그램 크기 확인 (주가 대비 비율)
        df['hist_pct'] = np.abs(df['histogram'] / df['close'])
        
        # 7. 추세 확인 - 히스토그램 방향과 이동평균 추세 확인
        df['trend_confirmed'] = False
        df['ma_trend_up'] = df['ma_trend'].diff() > 0  # 이동평균 상승 여부
        
        if self._trend_confirmation_period > 0:
            # 이전 N일 동안의 히스토그램 방향 일관성 검사
            for i in range(self._trend_confirmation_period, len(df)):
                if not valid_idx.iloc[i]:
                    continue
                    
                # 현재 히스토그램 부호
                current_hist_sign = np.sign(df['histogram'].iloc[i])
                current_raw_signal = df['raw_signal'].iloc[i]
                
                # 이전 N일 동안의 히스토그램이 현재와 같은 방향인지 확인
                consistent_trend = True
                for j in range(1, self._trend_confirmation_period + 1):
                    if i-j < 0 or not valid_idx.iloc[i-j]:
                        consistent_trend = False
                        break
                        
                    if np.sign(df['histogram'].iloc[i-j]) != current_hist_sign:
                        consistent_trend = False
                        break
                
                # 이동평균 추세와 신호 방향 일치 여부 확인
                ma_trend_aligned = True
                if current_raw_signal == 1 and not df['ma_trend_up'].iloc[i]:
                    ma_trend_aligned = False  # 매수 신호인데 이동평균 하락
                elif current_raw_signal == -1 and df['ma_trend_up'].iloc[i]:
                    ma_trend_aligned = False  # 매도 신호인데 이동평균 상승
                
                # 히스토그램 크기 충분한지 확인
                hist_size_sufficient = df['hist_pct'].iloc[i] >= self._min_histogram_value
                
                # 모든 조건을 만족해야 추세 확인됨
                df.loc[df.index[i], 'trend_confirmed'] = consistent_trend and ma_trend_aligned and hist_size_sufficient
        else:
            # 추세 확인을 건너뛰면 모든 신호를 확인된 것으로 처리
            df['trend_confirmed'] = True
        
        # 8. 필터링된 신호 생성
        df['signal'] = 0
        
        # 9. 임계값 이상의 크로스오버 및 추세 확인된 신호만 생성
        for i in range(len(df)):
            if not valid_idx.iloc[i]:
                continue
                
            if (df['raw_signal'].iloc[i] == 1 and 
                df['crossover_strength'].iloc[i] > self._min_crossover_threshold and
                df['trend_confirmed'].iloc[i]):
                df.loc[df.index[i], 'signal'] = 1
            elif (df['raw_signal'].iloc[i] == -1 and 
                  df['crossover_strength'].iloc[i] > self._min_crossover_threshold and
                  df['trend_confirmed'].iloc[i]):
                df.loc[df.index[i], 'signal'] = -1
        
        # 10. 최소 포지션 유지 기간 적용
        if self._min_holding_period > 0:
            last_trade_idx = -1
            last_trade_type = 0
            
            for i in range(len(df)):
                if not valid_idx.iloc[i]:
                    continue
                    
                if df['signal'].iloc[i] != 0:  # 신호가 있으면
                    if last_trade_idx >= 0 and (i - last_trade_idx) < self._min_holding_period:
                        # 최소 유지 기간 내에 있으면 신호 무시
                        df.loc[df.index[i], 'signal'] = 0
                    else:
                        # 새로운 거래 기록
                        last_trade_idx = i
                        last_trade_type = df['signal'].iloc[i]
        
        # 11. 신호 변화 감지
        df['position'] = df['signal'].diff()
        
        # 12. 첫 번째 유효한 신호에 대한 포지션 직접 설정
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
            "short_window": self._short_window,
            "long_window": self._long_window,
            "signal_window": self._signal_window,
            "min_crossover_threshold": self._min_crossover_threshold,
            "min_holding_period": self._min_holding_period,
            "trend_confirmation_period": self._trend_confirmation_period,
            "min_histogram_value": self._min_histogram_value,
            "ma_trend_period": self._ma_trend_period
        } 