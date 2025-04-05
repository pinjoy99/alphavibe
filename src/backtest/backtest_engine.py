import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
from dotenv import load_dotenv

from src.strategies import BaseStrategy, create_strategy
from src.visualization import plot_backtest_results as viz_plot_backtest_results

def backtest_strategy(df: pd.DataFrame, initial_capital: float) -> Dict[str, Any]:
    """
    백테스팅 전략 실행
    
    Parameters:
        df (pd.DataFrame): 전략이 적용된 데이터프레임
        initial_capital (float): 초기 자본금
    
    Returns:
        Dict[str, Any]: 백테스팅 결과
    """
    # 데이터 전처리 - NaN 값이 있는 행 제거
    required_columns = ['signal', 'position']
    df = df.copy()
    
    # NaN 체크 및 경고
    nan_rows = df[required_columns].isna().any(axis=1).sum()
    if nan_rows > 0:
        print(f"경고: 데이터에 {nan_rows}개의 NaN 행이 있습니다. 이 행들은 백테스팅에서 무시됩니다.")
    
    # 기본 변수 초기화
    position = 0  # 0: 매수 없음, 1: 매수
    cash = initial_capital
    coin_amount = 0
    fee_rate = 0.0005  # 수수료 0.05%
    max_invest_ratio = 0.5  # 최대 투자 비율 50% (리스크 관리)
    
    # 결과 저장용 리스트
    dates = []
    cash_history = []
    asset_history = []
    position_history = []
    trade_history = []
    
    # 백테스팅 실행
    for i in range(len(df)):
        date = df.index[i]
        # 정수 인덱스 대신 .iloc 사용하여 경고 제거
        price = df['close'].iloc[i]
        
        # NaN 값 처리 - signal 또는 position이 NaN인 경우 신호 무시
        if pd.isna(df['signal'].iloc[i]) or pd.isna(df['position'].iloc[i]):
            # 현재 상태 유지하며 자산 가치만 업데이트
            coin_value = coin_amount * price
            asset_value = cash + coin_value
            
            # 결과 저장
            dates.append(date)
            cash_history.append(cash)
            asset_history.append(asset_value)
            position_history.append(position)
            continue
            
        signal = df['signal'].iloc[i]
        
        # 당일 자산 가치 계산 (현금 + 코인 가치)
        coin_value = coin_amount * price
        asset_value = cash + coin_value
        
        # 신호에 따른 거래 실행
        if signal == 1 and position == 0:  # 매수 신호 & 미보유 상태
            # 최대 투자 비율을 고려한 투자금액 계산
            invest_amount = cash * max_invest_ratio
            # 수수료를 고려한 실제 코인 구매량
            coin_to_buy = (invest_amount * (1 - fee_rate)) / price
            # 현금 감소
            cash -= invest_amount
            # 코인 수량 증가
            coin_amount += coin_to_buy
            # 포지션 변경
            position = 1
            # 거래 기록
            trade_history.append({"date": date, "type": "buy", "price": price})
        
        elif signal == -1 and position == 1:  # 매도 신호 & 보유 상태
            # 코인 매도로 얻는 현금 (수수료 차감)
            cash_gained = coin_amount * price * (1 - fee_rate)
            # 현금 증가
            cash += cash_gained
            # 코인 수량 초기화
            coin_amount = 0
            # 포지션 변경
            position = 0
            # 거래 기록
            trade_history.append({"date": date, "type": "sell", "price": price})
        
        # 자산 가치 다시 계산 (거래 후)
        coin_value = coin_amount * price
        asset_value = cash + coin_value
        
        # 자산 가치가 너무 작으면 안전장치 (0으로 떨어지지 않도록)
        if asset_value < initial_capital * 0.01:  # 초기 자본금의 1% 이하로 떨어지면
            asset_value = initial_capital * 0.01  # 안전장치
        
        # 결과 저장
        dates.append(date)
        cash_history.append(cash)
        asset_history.append(asset_value)
        position_history.append(position)
    
    # 결과 데이터프레임 생성
    results_df = pd.DataFrame({
        'date': dates,
        'cash': cash_history,
        'asset': asset_history,
        'position': position_history
    })
    results_df.set_index('date', inplace=True)
    
    # 드로우다운 계산
    results_df['peak'] = results_df['asset'].cummax()
    results_df['drawdown'] = (results_df['asset'] - results_df['peak']) / results_df['peak'] * 100
    
    # 성과 지표 계산
    start_date = df.index[0].strftime('%Y-%m-%d')
    end_date = df.index[-1].strftime('%Y-%m-%d')
    total_days = (df.index[-1] - df.index[0]).days
    
    initial_asset = initial_capital
    final_asset = results_df['asset'].iloc[-1]
    
    total_return = final_asset - initial_asset
    total_return_pct = (total_return / initial_asset) * 100
    
    # 연평균 수익률 계산
    years = total_days / 365
    annual_return_pct = ((1 + total_return_pct / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
    
    # 최대 낙폭 계산
    max_drawdown_pct = results_df['drawdown'].min()
    
    # 거래 횟수
    trade_count = len(trade_history)
    
    # 결과 반환
    return {
        'df': df,  # 원본 데이터프레임
        'results_df': results_df,  # 결과 데이터프레임
        'trade_history': trade_history,  # 거래 기록
        'start_date': start_date,  # 시작일
        'end_date': end_date,  # 종료일
        'total_days': total_days,  # 총 일수
        'initial_capital': initial_capital,  # 초기 자본금
        'final_capital': final_asset,  # 최종 자본금
        'total_return': total_return,  # 총 수익
        'total_return_pct': total_return_pct,  # 총 수익률
        'annual_return_pct': annual_return_pct,  # 연간 수익률
        'max_drawdown_pct': max_drawdown_pct,  # 최대 낙폭
        'trade_count': trade_count  # 거래 횟수
    }

def plot_backtest_results(ticker: str, results: Dict[str, Any]) -> str:
    """
    백테스팅 결과 시각화 (시각화 모듈을 사용하는 래퍼 함수)
    
    Parameters:
        ticker (str): 종목 심볼
        results (Dict[str, Any]): 백테스팅 결과
    
    Returns:
        str: 저장된 차트 경로
    """
    # 환경 변수 로드
    load_dotenv()
    
    # 백테스트 결과 저장 경로
    backtest_result_path = os.getenv('BACKTEST_RESULT_PATH', 'results/strategy_results')
    
    # 시각화 모듈의 함수 사용
    return viz_plot_backtest_results(ticker, results, chart_dir=backtest_result_path)

def process_backtest_results(df: pd.DataFrame, results_df: pd.DataFrame, strategy: str, initial_capital: float, 
                      period: str, strategy_params: Dict = None) -> Dict[str, Any]:
    """
    백테스팅 결과 처리
    
    Parameters:
        df (pd.DataFrame): 원본 데이터프레임
        results_df (pd.DataFrame): 백테스팅 결과 데이터프레임
        strategy (str): 전략 이름
        initial_capital (float): 초기 자본금
        period (str): 백테스팅 기간
        strategy_params (Dict): 전략 파라미터
        
    Returns:
        Dict[str, Any]: 백테스팅 결과 데이터
    """
    # 거래 기록 추출
    trade_history = []
    for i in range(1, len(results_df)):
        # 매수 거래
        if results_df['position'].iloc[i-1] == 0 and results_df['position'].iloc[i] == 1:
            trade_history.append({
                'type': 'buy',
                'date': results_df.index[i],
                'price': df['close'].iloc[i],
                'amount': results_df['amount'].iloc[i]
            })
        # 매도 거래
        elif results_df['position'].iloc[i-1] == 1 and results_df['position'].iloc[i] == 0:
            trade_history.append({
                'type': 'sell',
                'date': results_df.index[i],
                'price': df['close'].iloc[i],
                'amount': results_df['amount'].iloc[i-1]  # 이전 보유량
            })
    
    # 요약 지표 계산
    start_date = df.index[0].strftime('%Y-%m-%d')
    end_date = df.index[-1].strftime('%Y-%m-%d')
    
    # 총 일수 계산
    total_days = (df.index[-1] - df.index[0]).days
    
    # 초기 및 최종 자산 가치
    initial_asset = initial_capital
    final_asset = results_df['asset'].iloc[-1]
    
    # 수익률 계산
    total_return = final_asset - initial_asset
    total_return_pct = (total_return / initial_asset) * 100
    
    # 연간 수익률 계산 (복리)
    if total_days > 0:
        annual_return_pct = (((1 + (total_return_pct / 100)) ** (365 / total_days)) - 1) * 100
    else:
        annual_return_pct = 0
    
    # 최대 낙폭 (MDD) 계산
    max_drawdown_pct = results_df['drawdown'].min()
    
    # 총 거래 횟수
    trade_count = len([t for t in trade_history if t['type'] == 'buy'])
    
    # 결과 반환
    return {
        'df': df,  # 원본 데이터
        'results_df': results_df,  # 백테스팅 결과 데이터
        'trade_history': trade_history,  # 거래 내역
        'strategy': strategy,  # 전략 이름
        'strategy_params': strategy_params,  # 전략 파라미터
        'start_date': start_date,  # 시작일
        'end_date': end_date,  # 종료일
        'total_days': total_days,  # 총 일수
        'initial_capital': initial_capital,  # 초기 자본금
        'final_capital': final_asset,  # 최종 자본금
        'total_return': total_return,  # 총 수익
        'total_return_pct': total_return_pct,  # 총 수익률
        'annual_return_pct': annual_return_pct,  # 연간 수익률
        'max_drawdown_pct': max_drawdown_pct,  # 최대 낙폭
        'trade_count': trade_count  # 거래 횟수
    } 