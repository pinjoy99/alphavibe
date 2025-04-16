from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib

logger = logging.getLogger(__name__)

class BaseStrategy(Strategy):
    """기본 전략 클래스"""
    def init(self):
        """전략 초기화"""
        pass

    def next(self):
        """다음 캔들에서의 전략 실행"""
        pass

# (내부 테스트용 전략, CODE 등 메타데이터 속성 제거)
class SMAStrategy(BaseStrategy):
    """단순 이동평균선 교차 전략 (내부 테스트용)"""
    def init(self):
        price = self.data.Close
        self.short_ma = self.I(talib.SMA, price, self.short_window)
        self.long_ma = self.I(talib.SMA, price, self.long_window)

    def next(self):
        if crossover(self.short_ma, self.long_ma):
            self.buy()
        elif crossover(self.long_ma, self.short_ma):
            self.sell()

class MACDStrategy(BaseStrategy):
    """MACD 교차 전략 (내부 테스트용)"""
    def init(self):
        price = self.data.Close
        macd_line, signal_line, _ = talib.MACD(price, 
                                              fastperiod=self.fast_period,
                                              slowperiod=self.slow_period,
                                              signalperiod=self.signal_period)
        self.macd = self.I(lambda x: macd_line)
        self.signal = self.I(lambda x: signal_line)

    def next(self):
        if crossover(self.macd, self.signal):
            self.buy()
        elif crossover(self.signal, self.macd):
            self.sell()

def run_backtest(df: pd.DataFrame,
                strategy_name: str,
                initial_capital: float,
                params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    백테스팅 실행 (캐싱 적용)
    
    Args:
        df: OHLCV 데이터프레임
        strategy_name: 전략 이름 ('sma' 또는 'macd')
        initial_capital: 초기 자본금
        params: 전략 파라미터
    
    Returns:
        백테스팅 결과
    """
    try:
        from src.utils.cache_manager import CacheManager
        
        logger.info(f"백테스팅 시작: {strategy_name}, 초기자본: {initial_capital:,}원")
        
        # 캐시 매니저 초기화
        cache_manager = CacheManager()
        
        # 캐시 키 구성
        cache_key = {
            "strategy": strategy_name,
            "initial_capital": initial_capital,
            "params": params,
            "data_hash": hash(df.to_json()),  # 데이터프레임의 해시값
            "type": "backtest_result"
        }
        
        # 캐시에서 결과 로드 시도 (최대 1시간 유효)
        cached_result = cache_manager.load_from_cache(
            cache_key,
            max_age=timedelta(hours=1)
        )
        
        if cached_result is not None:
            logger.info(f"캐시에서 백테스트 결과 로드: {strategy_name}")
            return cached_result
        
        # 기본 파라미터 설정
        default_params = {
            'sma': {'short_window': 10, 'long_window': 30},
            'macd': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
        }
        
        # 사용자 파라미터로 업데이트
        strategy_params = default_params[strategy_name]
        if params:
            strategy_params.update(params)
        
        # 전략 선택 (StrategyRegistry에서 동적으로 가져오기)
        from src.strategies.strategy_registry import StrategyRegistry
        strategy_class = StrategyRegistry.get_strategy_class(strategy_name)
        
        if not strategy_class:
            raise ValueError(f"지원하지 않는 전략: {strategy_name}")
        
        # 백테스팅 실행
        bt = Backtest(df, strategy_class, cash=initial_capital, commission=.002)
        result = bt.run(**strategy_params)
        
        # 결과 포맷팅
        trades_df = result._trades
        equity_curve = result._equity_curve
        
        # 매수/매도 시그널 추출
        buy_signals = trades_df[trades_df['Size'] > 0]['EntryPrice'].to_dict()
        sell_signals = trades_df[trades_df['Size'] < 0]['EntryPrice'].to_dict()
        
        # 데이터 포인트 생성
        data_points = []
        for index, row in df.iterrows():
            date_str = index.strftime('%Y-%m-%d')
            point = {
                'date': date_str,
                'price': row['Close'],
                'shortSMA': row['Short_MA'] if 'Short_MA' in row else None,
                'longSMA': row['Long_MA'] if 'Long_MA' in row else None,
                'volume': row['Volume'],
                'portfolio': equity_curve.loc[index, 'Equity'],
                'buySignal': buy_signals.get(index, None),
                'sellSignal': sell_signals.get(index, None)
            }
            data_points.append(point)
        
        # 요약 정보 생성
        summary = {
            'initialCapital': initial_capital,
            'finalCapital': result['Equity Final [$]'],
            'totalReturn': result['Return [%]'],
            'maxDrawdown': result['Max. Drawdown [%]'],
            'totalTrades': result['# Trades'],
            'winRate': result['Win Rate [%]'],
            'profitLossRatio': result['Profit Factor']
        }
        
        # 결과 생성
        backtest_result = {
            'data': data_points,
            'summary': summary
        }
        
        # 캐시에 저장
        cache_manager.save_to_cache(
            backtest_result,
            cache_key,
            max_age=timedelta(hours=1)
        )
        
        logger.info(f"백테스팅 완료: 수익률 {summary['totalReturn']:.2f}%, 승률 {summary['winRate']:.2f}%")
        
        return backtest_result
        
    except Exception as e:
        logger.error(f"백테스팅 중 에러 발생: {str(e)}")
        raise
