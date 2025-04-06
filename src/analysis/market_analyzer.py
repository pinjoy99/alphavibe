"""
시장 분석 핵심 클래스

암호화폐 시장 데이터를 분석하는 클래스를 제공합니다.
"""

import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
import os
from datetime import datetime

class MarketAnalyzer:
    """암호화폐 시장 분석을 수행하는 클래스"""
    
    def __init__(self, ticker: str, period: str = "3m", interval: str = "day"):
        """
        Parameters:
            ticker (str): 종목 심볼 (예: "KRW-BTC")
            period (str): 분석 기간 (예: "1d", "1w", "1m", "3m")
            interval (str): 데이터 간격 (예: "day", "minute60")
        """
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.data = None
        self.data_with_indicators = None
        self.analysis_results = {}
    
    def fetch_data(self) -> pd.DataFrame:
        """
        시장 데이터 조회
        
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        from src.api.upbit_api import get_backtest_data
        
        print(f"{self.ticker} 데이터 조회 중... (기간: {self.period}, 간격: {self.interval})")
        self.data = get_backtest_data(self.ticker, self.period, self.interval)
        
        if self.data is None or self.data.empty:
            print(f"{self.ticker} 데이터 조회 실패")
            return pd.DataFrame()
            
        return self.data
    
    def calculate_indicators(self) -> pd.DataFrame:
        """
        기술적 지표 계산
        
        Returns:
            pd.DataFrame: 지표가 추가된 데이터프레임
        """
        if self.data is None or self.data.empty:
            self.fetch_data()
            
        if self.data is None or self.data.empty:
            return pd.DataFrame()
            
        from src.indicators import calculate_indicators
        
        print(f"{self.ticker} 기술적 지표 계산 중...")
        self.data_with_indicators = calculate_indicators(self.data)
        
        return self.data_with_indicators
    
    def analyze(self) -> Dict[str, Any]:
        """
        기술적 분석 수행
        
        Returns:
            Dict[str, Any]: 분석 결과 및 메타데이터
        """
        if self.data_with_indicators is None:
            self.calculate_indicators()
            
        if self.data_with_indicators is None or self.data_with_indicators.empty:
            return {'error': f"{self.ticker} 분석을 위한 데이터가 없습니다."}
            
        # 기술적 분석 수행
        from src.analysis.technical_analysis import analyze_technical_indicators, analyze_support_resistance
        
        print(f"{self.ticker} 기술적 분석 수행 중...")
        
        # 지표 기반 분석
        tech_analysis = analyze_technical_indicators(self.data_with_indicators)
        
        # 지지/저항선 분석
        sr_levels = analyze_support_resistance(self.data_with_indicators)
        
        # 기본 통계 계산
        stats = {
            'start_date': self.data_with_indicators.index[0].strftime('%Y-%m-%d'),
            'end_date': self.data_with_indicators.index[-1].strftime('%Y-%m-%d'),
            'highest_price': self.data_with_indicators['High'].max(),
            'lowest_price': self.data_with_indicators['Low'].min(),
            'current_price': self.data_with_indicators['Close'].iloc[-1],
            'price_change': self.data_with_indicators['Close'].iloc[-1] - self.data_with_indicators['Close'].iloc[-2],
            'volume': self.data_with_indicators['Volume'].sum()
        }
        
        # 가격 변화율 계산
        stats['price_pct_change'] = (stats['price_change'] / self.data_with_indicators['Close'].iloc[-2]) * 100
        
        # 결과 구성
        self.analysis_results = {
            'ticker': self.ticker,
            'period': self.period,
            'interval': self.interval,
            'stats': stats,
            'technical_indicators': tech_analysis,
            'support_levels': sr_levels['support'],
            'resistance_levels': sr_levels['resistance'],
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.analysis_results
    
    def visualize(self) -> str:
        """
        기술적 분석 결과 시각화
        
        Returns:
            str: 생성된 차트 파일 경로
        """
        if self.data_with_indicators is None or self.data_with_indicators.empty:
            print(f"{self.ticker} 시각화를 위한 데이터가 없습니다.")
            return ""
            
        from src.visualization.analysis_charts import plot_market_analysis
        from src.utils.config import CHART_SAVE_PATH
        
        print(f"{self.ticker} 차트 생성 중...")
        
        # 데이터프레임 컬럼 표준화
        df = self.data_with_indicators.copy()
        
        # 데이터프레임 컬럼 확인 및 디버깅
        print(f"시각화 전 데이터프레임 컬럼: {df.columns.tolist()}")
        
        # 소문자 컬럼명으로 일관성 유지
        df.columns = [col.lower() if isinstance(col, str) else col for col in df.columns]
        
        try:
            # 차트 저장 경로 설정
            chart_dir = CHART_SAVE_PATH
            
            # 차트 파일 경로 생성
            file_name = f"{self.ticker}_{self.period}_{self.interval}_analysis.png"
            chart_path = os.path.join(chart_dir, file_name)
            
            # 분석 차트 생성
            chart_path = plot_market_analysis(
                df=df, 
                ticker=self.ticker, 
                chart_dir=chart_dir, 
                style='tradingview',  # 일관된 스타일 사용
                interval=self.interval,
                period=self.period
            )
            
            return chart_path
            
        except Exception as e:
            print(f"{self.ticker} 분석 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return "" 