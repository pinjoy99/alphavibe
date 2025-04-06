import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dotenv import load_dotenv

from src.strategies import BaseStrategy, create_strategy
from src.visualization.backtest_charts import plot_backtest_results as viz_plot_backtest_results
from src.utils.config import BACKTEST_CHART_PATH

def backtest_strategy(
    df: pd.DataFrame, 
    strategy_func,
    initial_capital: float,
    strategy_name: str,
    ticker: str,
    plot_results: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    전략 백테스팅 실행
    
    Parameters:
        df (pd.DataFrame): 가격 데이터
        strategy_func (Callable): 전략 함수
        initial_capital (float): 초기 자본금
        strategy_name (str): 전략 이름
        ticker (str): 거래 종목
        plot_results (bool): 결과 시각화 여부
        **kwargs: 전략 함수에 전달할 추가 매개변수
        
    Returns:
        Dict[str, Any]: 백테스팅 결과 및 성능 지표
    """
    # 데이터 복사
    df = df.copy()
    
    # 데이터가 충분한지 확인
    if len(df) < 10:
        print(f"경고: 데이터가 충분하지 않습니다. (길이: {len(df)})")
        return {'error': 'insufficient_data'}
    
    # 전략 적용
    try:
        # 데이터 컬럼 검사
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns and col.capitalize() not in df.columns:
                print(f"경고: 필수 컬럼 '{col}'이 데이터에 없습니다.")
                return {'error': 'missing_required_column'}
        
        # 소문자로 컬럼명 통일
        df.columns = [col.lower() if isinstance(col, str) else col for col in df.columns]
        
        # 전략 함수 호출
        print(f"전략 실행: {strategy_name}")
        signals = strategy_func(df, **kwargs)
        
    except Exception as e:
        print(f"전략 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return {'error': 'strategy_execution_failed', 'message': str(e)}
    
    # 신호 검증
    if signals is None or signals.empty:
        print(f"경고: 신호가 생성되지 않았습니다.")
        return {'error': 'no_signals_generated'}
    
    # 중복 인덱스 제거
    signals = signals[~signals.index.duplicated(keep='first')]
    
    # 백테스팅 초기화
    cash = initial_capital
    coin_amount = 0
    
    # 현금 및 코인 수량 내역
    cash_history = []
    coin_amount_history = []
    trade_history = []
    position_ratio_history = []
    
    # 최대 자산가치 (드로우다운 계산용)
    peak_asset = initial_capital
    
    # 거래별 전략 실행
    for i, date in enumerate(df.index):
        # 해당 날짜의 데이터 가져오기
        current_price = df.loc[date, 'close']
        
        # 현재 자산가치 계산
        current_asset = cash + (coin_amount * current_price)
        
        # 최대 자산가치 업데이트
        if current_asset > peak_asset:
            peak_asset = current_asset
        
        # 드로우다운 계산 (%)
        drawdown = ((peak_asset - current_asset) / peak_asset) * 100 if peak_asset > 0 else 0
        
        # 포지션 비율 계산 (0: 현금 100%, 1: 코인 100%)
        position_ratio = (coin_amount * current_price) / current_asset if current_asset > 0 else 0
        
        # 히스토리 저장
        cash_history.append(cash)
        coin_amount_history.append(coin_amount)
        position_ratio_history.append(position_ratio)
        
        # 해당 날짜에 신호가 있는지 확인
        if date in signals.index:
            signal = signals.loc[date]
            
            # 여러 신호가 있는 경우 처리
            if isinstance(signal, pd.DataFrame):
                signals_on_date = signal
            else:
                signals_on_date = pd.DataFrame([signal])
            
            # 해당 날짜의 모든 신호 처리
            for _, signal_row in signals_on_date.iterrows():
                signal_type = signal_row.get('type', None)
                
                # 매수 신호
                if signal_type == 'buy' and cash > 0:
                    # 매수 수량/비율 확인
                    amount = signal_row.get('amount', None)
                    ratio = signal_row.get('ratio', 1.0)  # 기본값: 100%
                    
                    # 매수할 현금 계산
                    buy_cash = cash * ratio if amount is None else min(amount, cash)
                    
                    # 코인 매수
                    coin_to_buy = buy_cash / current_price
                    cash -= buy_cash
                    coin_amount += coin_to_buy
                    
                    # 거래 기록
                    trade_history.append({
                        'date': date,
                        'type': 'buy',
                        'price': current_price,
                        'amount': buy_cash,
                        'coin_amount': coin_to_buy
                    })
                    
                    print(f"매수: {date} - 가격: {current_price:,.0f}, 투자금: {buy_cash:,.0f}, 코인량: {coin_to_buy:.8f}")
                
                # 매도 신호
                elif signal_type == 'sell' and coin_amount > 0:
                    # 매도 수량/비율 확인
                    amount = signal_row.get('amount', None)
                    ratio = signal_row.get('ratio', 1.0)  # 기본값: 100%
                    
                    # 매도할 코인 계산
                    coin_to_sell = coin_amount * ratio if amount is None else min(amount, coin_amount)
                    
                    # 코인 매도
                    sell_cash = coin_to_sell * current_price
                    cash += sell_cash
                    coin_amount -= coin_to_sell
                    
                    # 거래 기록
                    trade_history.append({
                        'date': date,
                        'type': 'sell',
                        'price': current_price,
                        'amount': sell_cash,
                        'coin_amount': coin_to_sell
                    })
                    
                    print(f"매도: {date} - 가격: {current_price:,.0f}, 판매금: {sell_cash:,.0f}, 코인량: {coin_to_sell:.8f}")
    
    # 결과 데이터프레임 생성
    trade_df = pd.DataFrame(trade_history)
    if not trade_df.empty:
        trade_df['date'] = pd.to_datetime(trade_df['date'])
        trade_df.set_index('date', inplace=True)
    
    # 최종 자산 계산
    final_price = df['close'].iloc[-1]
    final_asset = cash + (coin_amount * final_price)
    total_return = ((final_asset - initial_capital) / initial_capital) * 100
    
    # 백테스팅 결과
    backtest_result = {
        'initial_capital': initial_capital,
        'final_asset': final_asset,
        'return_pct': total_return,
        'coin_balance': coin_amount,
        'cash_balance': cash,
        'total_trades': len(trade_history),
        'trade_history': trade_df,
        'cash_history': cash_history,
        'coin_amount_history': coin_amount_history,
        'position_ratio_history': position_ratio_history,
        'chart_path': None,
        'start_date': df.index[0].strftime('%Y-%m-%d') if len(df) > 0 else None,
        'end_date': df.index[-1].strftime('%Y-%m-%d') if len(df) > 0 else None,
        'total_days': (df.index[-1] - df.index[0]).days if len(df) > 0 else 0
    }
    
    # 성능 계산
    performance = calculate_performance(
        df=df,
        trade_df=trade_df,
        cash_history=cash_history,
        coin_amount_history=coin_amount_history,
        initial_capital=initial_capital
    )
    
    backtest_result.update(performance)
    
    # 결과 시각화
    if plot_results:
        try:
            from src.backtest.result_processor import visualize_results
            chart_path = visualize_results(
                df=df,
                signals=signals,
                cash_history=cash_history,
                coin_amount_history=coin_amount_history,
                strategy_name=strategy_name,
                ticker=ticker,
                initial_capital=initial_capital,
                chart_dir=BACKTEST_CHART_PATH
            )
            backtest_result['chart_path'] = chart_path
            print(f"백테스트 차트 저장됨: {chart_path}")
            
        except Exception as e:
            print(f"결과 시각화 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    return backtest_result

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

def calculate_performance(
    df: pd.DataFrame,
    trade_df: pd.DataFrame,
    cash_history: list,
    coin_amount_history: list,
    initial_capital: float
) -> Dict[str, Any]:
    """
    백테스트 결과의 성능 지표 계산
    
    Parameters:
        df (pd.DataFrame): 가격 데이터
        trade_df (pd.DataFrame): 거래 내역
        cash_history (list): 현금 내역
        coin_amount_history (list): 코인 수량 내역
        initial_capital (float): 초기 자본금
        
    Returns:
        Dict[str, Any]: 성능 지표
    """
    # 자산 가치 계산
    asset_history = []
    for i in range(min(len(df), len(cash_history), len(coin_amount_history))):
        price = df['close'].iloc[i]
        asset = cash_history[i] + coin_amount_history[i] * price
        asset_history.append(asset)
    
    # 데이터 길이가 충분한지 확인
    if len(asset_history) < 2:
        return {
            'max_drawdown_pct': 0.0,
            'annual_return_pct': 0.0,
            'sharpe_ratio': 0.0,
            'winning_ratio': 0.0,
            'avg_profit_per_trade': 0.0,
            'avg_loss_per_trade': 0.0
        }
    
    # 자산 시리즈
    asset_series = pd.Series(asset_history, index=df.index[:len(asset_history)])
    
    # 날짜 관련 계산
    start_date = df.index[0]
    end_date = df.index[-1]
    total_days = (end_date - start_date).days
    years = total_days / 365.0
    
    # 수익률 계산
    final_asset = asset_series.iloc[-1]
    total_return_pct = ((final_asset - initial_capital) / initial_capital) * 100
    
    # 연평균 수익률 계산
    annual_return_pct = (((1 + (total_return_pct / 100)) ** (1 / max(years, 0.01))) - 1) * 100
    
    # 일일 수익률
    daily_returns = asset_series.pct_change().dropna()
    
    # 변동성 계산
    volatility = daily_returns.std() * (252 ** 0.5)  # 연간화된 변동성
    
    # 샤프 비율 계산 (무위험 수익률은 0으로 가정)
    risk_free_rate = 0.02  # 연 2%로 가정
    daily_risk_free = (1 + risk_free_rate) ** (1 / 252) - 1
    excess_returns = daily_returns - daily_risk_free
    sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * (252 ** 0.5) if excess_returns.std() > 0 else 0
    
    # 드로우다운 계산
    peak = asset_series.cummax()
    drawdown = (asset_series - peak) / peak * 100
    max_drawdown_pct = drawdown.min()
    
    # 거래 관련 지표
    winning_trades = 0
    losing_trades = 0
    total_profit = 0
    total_loss = 0
    
    # 거래가 있는 경우
    if (isinstance(trade_df, pd.DataFrame) and 
        not trade_df.empty and 
        'type' in trade_df.columns):
        # 매수/매도 포인트 식별
        buy_points = trade_df[trade_df['type'] == 'buy']
        sell_points = trade_df[trade_df['type'] == 'sell']
        
        # 매수, 매도 매칭
        for i, sell in enumerate(sell_points.iterrows()):
            sell_date, sell_data = sell
            sell_price = sell_data['price']
            sell_amount = sell_data.get('coin_amount', 0)
            
            # 매도 이전의 매수 찾기
            prev_buys = buy_points[buy_points.index < sell_date]
            
            if not prev_buys.empty:
                latest_buy = prev_buys.iloc[-1]
                buy_price = latest_buy['price']
                
                # 수익/손실 계산
                profit_loss = (sell_price - buy_price) / buy_price * 100
                
                if profit_loss > 0:
                    winning_trades += 1
                    total_profit += profit_loss
                else:
                    losing_trades += 1
                    total_loss += abs(profit_loss)
    
    # 승률 계산
    total_completed_trades = winning_trades + losing_trades
    winning_ratio = (winning_trades / total_completed_trades) * 100 if total_completed_trades > 0 else 0
    
    # 평균 수익/손실
    avg_profit_per_trade = total_profit / winning_trades if winning_trades > 0 else 0
    avg_loss_per_trade = total_loss / losing_trades if losing_trades > 0 else 0
    
    # 승률과 손익비
    profit_loss_ratio = avg_profit_per_trade / avg_loss_per_trade if avg_loss_per_trade > 0 else 0
    
    # 결과 반환
    return {
        'max_drawdown_pct': max_drawdown_pct,
        'annual_return_pct': annual_return_pct,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'winning_ratio': winning_ratio,
        'avg_profit_per_trade': avg_profit_per_trade,
        'avg_loss_per_trade': avg_loss_per_trade,
        'profit_loss_ratio': profit_loss_ratio,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades
    } 