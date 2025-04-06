"""
시장 분석 모듈

암호화폐 시장 데이터의 기술적 분석을 수행하는 함수를 제공합니다.
"""

from .market_analyzer import MarketAnalyzer
from typing import Dict, Any, Optional

def analyze_market(
    ticker: str, 
    period: str = "3m", 
    interval: str = "day",
    indicator_config: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """
    암호화폐 시장 분석 수행
    
    Parameters:
        ticker (str): 종목 심볼 (예: "KRW-BTC")
        period (str): 분석 기간 (예: "1d", "1w", "1m", "3m")
        interval (str): 데이터 간격 (예: "day", "minute60")
        indicator_config (Optional[Dict[str, bool]]): 사용할 지표 설정
        
    Returns:
        Dict[str, Any]: 분석 결과 및 메타데이터
    """
    analyzer = MarketAnalyzer(ticker, period, interval)
    result = analyzer.analyze()
    
    # 차트 생성 (시각화 모듈 연동)
    chart_path = analyzer.visualize()
    
    # 결과에 차트 경로 추가
    result['chart_path'] = chart_path
    
    return result

# 외부에 공개할 함수 목록
__all__ = [
    'analyze_market',
    'MarketAnalyzer'
] 