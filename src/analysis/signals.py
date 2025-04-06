"""
매매 신호 모듈

기술적 분석을 기반으로 매매 신호를 생성하는 함수를 제공합니다.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

def generate_signals(df: pd.DataFrame, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    분석 결과를 기반으로 매매 신호 생성
    
    Parameters:
        df (pd.DataFrame): 지표가 계산된 데이터프레임
        analysis_results (Dict[str, Any]): 분석 결과
        
    Returns:
        Dict[str, Any]: 매매 신호 정보
    """
    signals = {}
    
    # 현재가 확인
    current_price = df['close'].iloc[-1] if 'close' in df.columns else df['Close'].iloc[-1]
    
    # 1. RSI 기반 신호
    if 'technical_indicators' in analysis_results and 'RSI' in analysis_results['technical_indicators']:
        rsi_analysis = analysis_results['technical_indicators']['RSI']
        
        if '과매수' in rsi_analysis:
            signals['rsi'] = {
                'signal': '매도',
                'strength': 'medium',
                'description': f'RSI 과매수 구간 - 매도 고려'
            }
        elif '과매도' in rsi_analysis:
            signals['rsi'] = {
                'signal': '매수',
                'strength': 'medium',
                'description': f'RSI 과매도 구간 - 매수 고려'
            }
    
    # 2. MACD 기반 신호
    if 'technical_indicators' in analysis_results and 'MACD' in analysis_results['technical_indicators']:
        macd_analysis = analysis_results['technical_indicators']['MACD']
        
        if '상승 추세 강화' in macd_analysis:
            signals['macd'] = {
                'signal': '매수',
                'strength': 'strong',
                'description': f'MACD 상승 추세 강화 - 매수 신호'
            }
        elif '하락 추세 강화' in macd_analysis:
            signals['macd'] = {
                'signal': '매도',
                'strength': 'strong',
                'description': f'MACD 하락 추세 강화 - 매도 신호'
            }
    
    # 3. 볼린저 밴드 신호
    if 'technical_indicators' in analysis_results and '볼린저 밴드' in analysis_results['technical_indicators']:
        bb_analysis = analysis_results['technical_indicators']['볼린저 밴드']
        
        if '상단 돌파' in bb_analysis:
            signals['bollinger'] = {
                'signal': '매도',
                'strength': 'medium',
                'description': f'볼린저 밴드 상단 돌파 - 매도 고려'
            }
        elif '하단 돌파' in bb_analysis:
            signals['bollinger'] = {
                'signal': '매수',
                'strength': 'medium',
                'description': f'볼린저 밴드 하단 돌파 - 매수 고려'
            }
    
    # 4. 지지선/저항선 기반 신호
    if 'support_levels' in analysis_results and analysis_results['support_levels']:
        nearest_support = analysis_results['support_levels'][0]
        support_proximity = (current_price - nearest_support) / current_price * 100
        
        if support_proximity < 3.0:  # 현재가가 지지선에 매우 가까움
            signals['support'] = {
                'signal': '매수',
                'strength': 'medium',
                'description': f'주요 지지선 접근 - 매수 고려',
                'price_level': nearest_support
            }
    
    if 'resistance_levels' in analysis_results and analysis_results['resistance_levels']:
        nearest_resistance = analysis_results['resistance_levels'][0]
        resistance_proximity = (nearest_resistance - current_price) / current_price * 100
        
        if resistance_proximity < 3.0:  # 현재가가 저항선에 매우 가까움
            signals['resistance'] = {
                'signal': '매도',
                'strength': 'medium',
                'description': f'주요 저항선 접근 - 매도 고려',
                'price_level': nearest_resistance
            }
    
    # 5. 종합 신호 생성
    buy_signals = [s for s in signals.values() if s['signal'] == '매수']
    sell_signals = [s for s in signals.values() if s['signal'] == '매도']
    
    # 강한 신호 우선
    strong_buy = [s for s in buy_signals if s['strength'] == 'strong']
    strong_sell = [s for s in sell_signals if s['strength'] == 'strong']
    
    # 종합 신호
    if len(strong_buy) > len(strong_sell):
        recommend = "매수"
    elif len(strong_sell) > len(strong_buy):
        recommend = "매도"
    elif len(buy_signals) > len(sell_signals):
        recommend = "매수 고려"
    elif len(sell_signals) > len(buy_signals):
        recommend = "매도 고려"
    else:
        recommend = "관망"
    
    signals['recommend'] = {
        'signal': recommend,
        'buy_signals': len(buy_signals),
        'sell_signals': len(sell_signals),
        'description': get_recommendation_description(recommend)
    }
    
    return signals

def get_recommendation_description(recommend: str) -> str:
    """
    추천에 대한 설명 생성
    
    Parameters:
        recommend (str): 추천 유형
        
    Returns:
        str: 설명 텍스트
    """
    descriptions = {
        "매수": "여러 지표가 강한 매수 신호를 나타내고 있습니다. 시장 상황을 고려하여 매수 검토가 가능합니다.",
        "매도": "여러 지표가 강한 매도 신호를 나타내고 있습니다. 시장 상황을 고려하여 매도 검토가 가능합니다.",
        "매수 고려": "일부 지표가 매수 신호를 보이고 있으나, 추가 확인이 필요합니다.",
        "매도 고려": "일부 지표가 매도 신호를 보이고 있으나, 추가 확인이 필요합니다.",
        "관망": "현재 뚜렷한 방향성이 보이지 않습니다. 추가 신호가 나타날 때까지 관망하는 것이 좋겠습니다."
    }
    
    return descriptions.get(recommend, "분석 결과를 검토하여 매매 결정을 내리세요.") 