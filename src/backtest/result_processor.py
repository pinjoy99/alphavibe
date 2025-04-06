import pandas as pd
import os
from datetime import datetime
from src.utils.config import BACKTEST_CHART_PATH

def visualize_results(
    df: pd.DataFrame,
    signals: pd.DataFrame,
    cash_history: list,
    coin_amount_history: list,
    strategy_name: str,
    ticker: str,
    initial_capital: float,
    chart_dir: str = BACKTEST_CHART_PATH,
    style: str = 'tradingview',
    **kwargs
) -> str:
    """
    백테스트 결과 시각화
    
    Parameters:
        df (pd.DataFrame): 가격 데이터
        signals (pd.DataFrame): 거래 신호
        cash_history (list): 현금 히스토리
        coin_amount_history (list): 코인 수량 히스토리
        strategy_name (str): 전략 이름
        ticker (str): 종목 심볼
        initial_capital (float): 초기 자본금
        chart_dir (str): 차트 저장 경로
        style (str): 차트 스타일
        **kwargs: 추가 키워드 인자
    
    Returns:
        str: 차트 파일 경로
    """
    # 기본 디렉토리 설정
    if not os.path.exists(chart_dir):
        os.makedirs(chart_dir)
    
    # 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # '@' 문자가 있다면 'KRW-'로 대체 (Upbit 티커 형식)
    safe_ticker = ticker.replace('@', 'KRW-') if '@' in ticker else ticker
    
    # 현재 백테스트 정보에서 기간과 인터벌 가져오기 (이 정보가 함수 인자에 없으므로 다음 행에서 추가)
    # 이 정보는 main.py에서 run_backtest 함수에서 처리될 때 결과에 이미 추가되어 있음
    period_info = kwargs.get('period', '')
    interval_info = kwargs.get('interval', '')
    period_str = f"_{period_info}" if period_info else ""
    interval_str = f"_{interval_info}" if interval_info else ""
    
    filename = f"{safe_ticker}_{strategy_name}{period_str}{interval_str}_{timestamp}.png"
    chart_path = os.path.join(chart_dir, filename)
    
    # 시각화 모듈 임포트
    from src.visualization.backtest_charts import plot_backtest_results
    
    # 스타일 설정 가져오기
    from src.visualization.styles import apply_style
    style_config = apply_style(style)
    
    # 차트 그리기
    print(f"백테스트 차트 생성 시작: {ticker} - {strategy_name} (스타일: {style})")
    plot_backtest_results(
        df=df,
        signals=signals,
        cash_history=cash_history,
        coin_amount_history=coin_amount_history,
        strategy_name=f"{strategy_name} ({ticker})",
        save_path=chart_path,
        style_config=style_config
    )
    print(f"백테스트 차트 저장 완료: {chart_path}")
    
    return chart_path 