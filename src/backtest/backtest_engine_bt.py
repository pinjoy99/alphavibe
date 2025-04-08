from backtesting import Backtest
import pandas as pd
from typing import Dict, Any, Type
from backtesting import Strategy
import numpy as np
from datetime import datetime
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from src.visualization.backtest_charts import plot_backtest_results
from src.utils.config import BACKTEST_CHART_PATH

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """RSI 계산"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def run_backtest_bt(
    df: pd.DataFrame,
    strategy_class: Type[Strategy],
    initial_capital: float,
    strategy_name: str,
    ticker: str,
    commission: float = 0.002,
    plot_results: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Backtesting.py를 사용한 전략 백테스팅 실행
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터
        strategy_class (Type[Strategy]): Backtesting.py Strategy 클래스
        initial_capital (float): 초기 자본금
        strategy_name (str): 전략 이름
        ticker (str): 거래 종목
        commission (float): 거래 수수료 (기본값: 0.002 = 0.2%)
        plot_results (bool): 결과 시각화 여부
        **kwargs: 전략 클래스에 전달할 추가 매개변수
        
    Returns:
        Dict[str, Any]: 백테스팅 결과 및 성능 지표
    """
    # 데이터 전처리
    df = df.copy()
    
    # 컬럼명 대문자로 변경 (Backtesting.py 요구사항)
    df.columns = [col.capitalize() if isinstance(col, str) else col for col in df.columns]
    
    # 데이터 간략 정보만 출력 
    print(f"\n데이터 정보: {len(df)}개 ({df.index[0]} ~ {df.index[-1]})")
    
    # 가격을 satoshi 단위로 변환 (1 BTC = 100,000,000 satoshi)
    # BTC 거래의 경우 작은 단위로 변환 (1/10000)
    if 'BTC' in ticker:
        scale_factor = 1000.0  # 가격을 1/1000로 조정 (천분의 1)
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                df[col] = df[col] / scale_factor
        
        # 초기 자본을 가격의 10배로 설정 (가격보다 훨씬 크게)
        adjusted_capital = df['Close'].max() * 10
        print(f"초기 자본 조정: {initial_capital / scale_factor:.1f} -> {adjusted_capital:.1f} (가격의 10배)")
        initial_capital = adjusted_capital
        
        # 변환 후 데이터의 세부 정보는 출력하지 않음
        # print("\n변환 후 데이터:")
        # print(df.head())
        print(f"변환 후 가격 범위: {df['Close'].min():.1f} ~ {df['Close'].max():.1f}")
        
        # 데이터 유효성 검증 간략화
        print(f"가격 < 초기자본: {(df['Close'] < initial_capital).sum()}/{len(df)}")
    
    # Backtesting 실행
    bt = Backtest(
        df,
        strategy_class,
        cash=initial_capital,
        commission=commission,
        exclusive_orders=True,
        trade_on_close=True,  # 종가 기준 거래 (더 안정적)
        hedging=True  # 헷징 허용 (여러 포지션 동시 보유)
    )
    
    # 디버깅 정보 출력
    print(f"\n백테스팅 설정: 초기자본={initial_capital:.1f}, 수수료={commission}, 파라미터={kwargs}")
    
    # 전략 파라미터 설정
    stats = bt.run(**kwargs)
    
    # 거래 내역 간략화
    trades = stats._trades
    print(f"\n거래 내역: {len(trades)}개")
    
    # 결과 처리
    # 거래 내역 데이터프레임 생성
    if len(trades) > 0:
        trade_history = pd.DataFrame({
            'date': pd.to_datetime(trades.EntryTime),
            'type': ['buy' if size > 0 else 'sell' for size in trades.Size],
            'price': trades.EntryPrice * (scale_factor if 'BTC' in ticker else 1),
            'amount': abs(trades.Size),
            'profit': trades.PnL * (scale_factor if 'BTC' in ticker else 1)
        })
        trade_history.set_index('date', inplace=True)
    else:
        trade_history = pd.DataFrame()
    
    # 백테스팅 결과
    backtest_result = {
        'initial_capital': initial_capital * (scale_factor if 'BTC' in ticker else 1),
        'final_asset': stats['Equity Final [$]'] * (scale_factor if 'BTC' in ticker else 1),
        'return_pct': stats['Return [%]'],
        'total_trades': stats['# Trades'],
        'win_rate': stats['Win Rate [%]'],
        'profit_factor': stats['Profit Factor'],
        'max_drawdown': stats['Max. Drawdown [%]'],
        'sharpe_ratio': stats['Sharpe Ratio'],
        'trade_history': trade_history,
        'chart_path': None,
        'start_date': df.index[0].strftime('%Y-%m-%d') if len(df) > 0 else None,
        'end_date': df.index[-1].strftime('%Y-%m-%d') if len(df) > 0 else None,
        'total_days': (df.index[-1] - df.index[0]).days if len(df) > 0 else 0
    }
    
    # 결과 시각화
    if plot_results:
        try:
            # 차트 생성
            fig = plt.figure(figsize=(15, 12), facecolor='#131722')
            gs = gridspec.GridSpec(5, 1, height_ratios=[3, 1, 1, 1, 1])
            
            # 1. 가격 차트 및 매매 시그널
            ax1 = plt.subplot(gs[0])
            ax1.plot(df.index, df['Close'], color='white', linewidth=1, label='가격')
            
            # 이동평균선 표시 (디버깅용)
            if 'short_window' in kwargs and 'long_window' in kwargs:
                short_ma = df['Close'].rolling(kwargs['short_window']).mean()
                long_ma = df['Close'].rolling(kwargs['long_window']).mean()
                ax1.plot(df.index, short_ma, color='#ff9500', linewidth=1, alpha=0.8, label=f'SMA({kwargs["short_window"]})')
                ax1.plot(df.index, long_ma, color='#5856d6', linewidth=1, alpha=0.8, label=f'SMA({kwargs["long_window"]})')
            
            # 매매 시그널 표시 - 내부 인디케이터에서 생성된 시그널 사용
            # 이 부분은 Backtesting.py 내부 로직에 따라 달라질 수 있음
            signals = stats.get('_strategy')
            if signals is not None:
                try:
                    # 인디케이터에서 생성된 매수/매도 시그널 사용
                    if hasattr(signals, 'buy_signals') and hasattr(signals, 'sell_signals'):
                        buy_indices = [i for i, val in enumerate(signals.buy_signals) if val > 0]
                        sell_indices = [i for i, val in enumerate(signals.sell_signals) if val > 0]
                        
                        if buy_indices:
                            buy_dates = [df.index[i] for i in buy_indices if i < len(df.index)]
                            buy_prices = [df['Close'][i] for i in buy_indices if i < len(df['Close'])]
                            ax1.scatter(buy_dates, buy_prices, marker='^', color='#4CD964', s=100, label='매수 (내부)')
                            print(f"매수 시그널: {len(buy_dates)}개")
                        
                        if sell_indices:
                            sell_dates = [df.index[i] for i in sell_indices if i < len(df.index)]
                            sell_prices = [df['Close'][i] for i in sell_indices if i < len(df['Close'])]
                            ax1.scatter(sell_dates, sell_prices, marker='v', color='#FF3B30', s=100, label='매도 (내부)')
                            print(f"매도 시그널: {len(sell_dates)}개")
                except Exception as e:
                    print(f"내부 시그널 사용 중 오류: {e}")
            
            # 거래 내역에서 시그널 표시
            if not trade_history.empty:
                buy_signals = trade_history[trade_history['type'] == 'buy']
                sell_signals = trade_history[trade_history['type'] == 'sell']
                
                if not buy_signals.empty:
                    ax1.scatter(buy_signals.index, buy_signals['price'] / (scale_factor if 'BTC' in ticker else 1), 
                              marker='^', color='#4CD964', s=120, label='매수')
                    print(f"매수 거래: {len(buy_signals)}개")
                
                if not sell_signals.empty:
                    ax1.scatter(sell_signals.index, sell_signals['price'] / (scale_factor if 'BTC' in ticker else 1), 
                              marker='v', color='#FF3B30', s=120, label='매도')
                    print(f"매도 거래: {len(sell_signals)}개")
            
            ax1.set_title(f'{strategy_name} 백테스팅 결과 ({ticker})', color='white', pad=20)
            ax1.grid(True, alpha=0.2)
            ax1.legend()
            
            # 2. 거래량 차트
            ax2 = plt.subplot(gs[1], sharex=ax1)
            ax2.bar(df.index, df['Volume'], color='#1f77b4', alpha=0.5)
            ax2.set_title('거래량', color='white')
            ax2.grid(True, alpha=0.2)
            
            # 3. RSI 차트
            ax3 = plt.subplot(gs[2], sharex=ax1)
            rsi = calculate_rsi(df['Close'])
            ax3.plot(df.index, rsi, color='#FF9500', linewidth=1)
            ax3.axhline(y=70, color='#FF3B30', linestyle='--', alpha=0.5)
            ax3.axhline(y=30, color='#4CD964', linestyle='--', alpha=0.5)
            ax3.set_title('RSI (14)', color='white')
            ax3.grid(True, alpha=0.2)
            
            # 4. 자산 가치 차트
            ax4 = plt.subplot(gs[3], sharex=ax1)
            equity_curve = pd.Series(stats['_equity_curve'].Equity, index=df.index)
            ax4.plot(df.index, equity_curve, color='#5856D6', linewidth=1)
            ax4.set_title('포트폴리오 가치', color='white')
            ax4.grid(True, alpha=0.2)
            
            # 5. 드로우다운 차트
            ax5 = plt.subplot(gs[4], sharex=ax1)
            drawdown = pd.Series(stats['_equity_curve'].DrawdownPct, index=df.index)
            ax5.fill_between(df.index, drawdown, 0, color='#FF3B30', alpha=0.3)
            ax5.set_title('드로우다운 (%)', color='white')
            ax5.grid(True, alpha=0.2)
            
            # 공통 스타일 설정
            for ax in [ax1, ax2, ax3, ax4, ax5]:
                ax.set_facecolor('#131722')
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['left'].set_color('white')
                ax.spines['right'].set_color('white')
            
            # 레이아웃 조정
            plt.tight_layout()
            
            # 차트 저장
            chart_path = os.path.join(
                BACKTEST_CHART_PATH, 
                f"{ticker}_{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            plt.savefig(chart_path, dpi=100, bbox_inches='tight', facecolor='#131722')
            backtest_result['chart_path'] = chart_path
            
            print(f"백테스트 차트 저장됨: {chart_path}")
            
        except Exception as e:
            print(f"결과 시각화 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    return backtest_result 