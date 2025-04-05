import pyupbit
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import sys
import argparse
from dotenv import load_dotenv
from telegram import Bot
import asyncio
from typing import Optional, Dict, Any, List
import numpy as np
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import koreanize_matplotlib  # 한글 폰트 적용
from src.api.upbit_api import get_historical_data, parse_period_to_datetime, get_backtest_data
from src.backtest import (
    backtest_strategy,
    plot_backtest_results
)
from src.strategies import create_strategy
from src.notification import (
    send_telegram_message,
    send_telegram_chart,
    get_telegram_backtest_message,
    get_telegram_analysis_message
)

# 시각화 모듈 추가
from src.visualization import (
    plot_price_chart,
    setup_chart_dir
)

# 명령줄 인자 파싱
def parse_args():
    parser = argparse.ArgumentParser(description="암호화폐 가격 분석")
    parser.add_argument("--telegram", "-t", action="store_true", help="텔레그램 알림 활성화")
    parser.add_argument("--backtest", "-b", action="store_true", help="백테스팅 모드 활성화")
    parser.add_argument("--strategy", "-s", choices=["sma", "bb", "macd", "rsi"], default="sma", help="백테스팅 전략 선택 (기본값: sma)")
    parser.add_argument("--period", "-p", type=str, default="3m", help="백테스팅 기간 (예: 1d, 3d, 1w, 1m, 3m, 6m, 1y)")
    parser.add_argument("--invest", "-i", type=float, default=1000000, help="백테스팅 초기 투자금액 (원화)")
    return parser.parse_args()

# Load environment variables
load_dotenv()

# Get settings from environment variables
CHART_SAVE_PATH = os.getenv('CHART_SAVE_PATH', 'results/analysis')
DEFAULT_INTERVAL = os.getenv('DEFAULT_INTERVAL', 'day')
DEFAULT_COUNT = int(os.getenv('DEFAULT_COUNT', '100'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# API key settings
UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')

# 백테스팅 설정
BACKTEST_DATA_PATH = os.getenv('BACKTEST_DATA_PATH', 'backtest_data')
BACKTEST_RESULT_PATH = os.getenv('BACKTEST_RESULT_PATH', 'results/strategy_results')

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------
# 백테스팅 실행 함수
# ----------------------

async def run_backtest(bot: Optional[Bot], ticker: str, strategy: str, period: str, initial_capital: float, enable_telegram: bool) -> None:
    """
    백테스팅 실행
    
    Parameters:
        bot (Optional[Bot]): 텔레그램 봇 인스턴스
        ticker (str): 종목 심볼
        strategy (str): 전략 이름
        period (str): 백테스팅 기간
        initial_capital (float): 초기 투자금액
        enable_telegram (bool): 텔레그램 알림 활성화 여부
    """
    print(f"\n백테스팅 시작: {ticker} (전략: {strategy}, 기간: {period})")
    
    if enable_telegram:
        await send_telegram_message(f"🔍 백테스팅 시작: {ticker} (전략: {strategy}, 기간: {period})", enable_telegram, bot)
    
    # 백테스팅 데이터 조회
    interval = "minute60"  # 1시간 간격 데이터 사용
    df = get_backtest_data(ticker, period, interval)
    
    if df is not None and not df.empty:
        # 전략 파라미터 설정
        strategy_params = {}
        if strategy == "sma":
            # SMA 파라미터 최적화 - 더 긴 이동평균선 기간 사용
            strategy_params = {
                "short_window": 10,  # 이전: 5
                "long_window": 30    # 이전: 20
            }
        elif strategy == "bb":
            # 볼린저 밴드 파라미터
            strategy_params = {
                "window": 20,
                "std_dev": 2.0
            }
        elif strategy == "macd":
            # MACD 파라미터
            strategy_params = {
                "short_window": 12,
                "long_window": 26,
                "signal_window": 9
            }
        elif strategy == "rsi":
            # RSI 파라미터
            strategy_params = {
                "window": 14,
                "overbought": 70,
                "oversold": 30
            }
        
        # 전략 객체 생성 및 적용
        strategy_obj = create_strategy(strategy, **strategy_params)
        if strategy_obj:
            # 전략 적용
            df = strategy_obj.apply(df)
            
            # 백테스팅 실행
            results = backtest_strategy(df, initial_capital)
            
            # 결과에 전략 정보 추가
            results['strategy'] = strategy_obj.name
            results['strategy_params'] = strategy_obj.params
            
            # 결과 출력
            print("\n백테스팅 결과:")
            print(f"전략: {strategy_obj.name}")
            print(f"기간: {results['start_date']} ~ {results['end_date']} ({results['total_days']}일)")
            print(f"초기 자본금: {results['initial_capital']:,.0f} KRW")
            print(f"최종 자본금: {results['final_capital']:,.0f} KRW")
            print(f"총 수익률: {results['total_return_pct']:.2f}%")
            print(f"연간 수익률: {results['annual_return_pct']:.2f}%")
            print(f"최대 낙폭: {results['max_drawdown_pct']:.2f}%")
            print(f"거래 횟수: {results['trade_count']}")
            
            # 백테스팅 결과 시각화
            chart_path = plot_backtest_results(ticker, results)
            print(f"차트 저장: {chart_path}")
            
            # 텔레그램 알림
            if enable_telegram:
                # 결과 메시지 작성
                params_str = ""
                if strategy == "sma":
                    params_str = f"(단기: {strategy_params['short_window']}, 장기: {strategy_params['long_window']})"
                elif strategy == "bb":
                    params_str = f"(기간: {strategy_params['window']}, 표준편차: {strategy_params['std_dev']})"
                elif strategy == "macd":
                    params_str = f"(단기: {strategy_params['short_window']}, 장기: {strategy_params['long_window']}, 시그널: {strategy_params['signal_window']})"
                elif strategy == "rsi":
                    params_str = f"(기간: {strategy_params['window']}, 과매수: {strategy_params['overbought']}, 과매도: {strategy_params['oversold']})"
                
                # 메시지 생성과 전송을 분리된 모듈 함수 사용
                result_message = get_telegram_backtest_message(ticker, strategy_obj.name, params_str, results)
                
                # 차트 전송
                await send_telegram_chart(chart_path, result_message, enable_telegram, bot)
        else:
            error_message = f"유효하지 않은 전략: {strategy}"
            print(error_message)
            if enable_telegram:
                await send_telegram_message(f"❌ {error_message}", enable_telegram, bot)
    else:
        error_message = f"백테스팅 데이터 조회 실패: {ticker}"
        print(error_message)
        if enable_telegram:
            await send_telegram_message(f"❌ {error_message}", enable_telegram, bot)

async def analyze_ticker(bot: Optional[Bot], ticker: str, enable_telegram: bool) -> None:
    """Analyze single ticker and send results to Telegram"""
    print(f"\nAnalyzing {ticker}...")
    
    if enable_telegram:
        await send_telegram_message(f"🔍 Starting analysis for {ticker}...", enable_telegram, bot)
    
    # Get historical data
    df = get_historical_data(ticker)
    
    if df is not None and not df.empty:
        # Prepare statistics
        stats = {
            'start_date': df.index[0].strftime('%Y-%m-%d'),
            'end_date': df.index[-1].strftime('%Y-%m-%d'),
            'highest_price': df['high'].max(),
            'lowest_price': df['low'].min(),
            'volume': df['volume'].sum()
        }
        
        # Print to console
        print("\nBasic Statistics:")
        print(f"Start Date: {stats['start_date']}")
        print(f"End Date: {stats['end_date']}")
        print(f"Highest Price: {stats['highest_price']:,.0f} KRW")
        print(f"Lowest Price: {stats['lowest_price']:,.0f} KRW")
        print(f"Total Volume: {stats['volume']:,.0f}")
        
        # 시각화 모듈의 함수 사용
        chart_dir = setup_chart_dir(CHART_SAVE_PATH)
        chart_path = plot_price_chart(df, ticker, chart_dir=chart_dir)
        print(f"Chart saved: {chart_path}")
        
        # Send to Telegram if enabled
        if enable_telegram:
            # 메시지 생성과 전송을 분리된 모듈 함수 사용
            stats_message = get_telegram_analysis_message(ticker, stats)
            await send_telegram_chart(chart_path, stats_message, enable_telegram, bot)
    else:
        error_message = f"Failed to fetch data for {ticker}"
        print(error_message)
        if enable_telegram:
            await send_telegram_message(f"❌ {error_message}", enable_telegram, bot)

async def main_async(args):
    # 명령줄 인자 추출
    enable_telegram = args.telegram
    enable_backtest = args.backtest
    strategy = args.strategy
    period = args.period
    initial_capital = args.invest
    
    # 시각화 모듈 사용하여 차트 디렉토리 설정
    charts_dir = setup_chart_dir(CHART_SAVE_PATH)
    
    # 백테스팅 결과 디렉토리 생성
    if enable_backtest:
        backtest_results_dir = setup_chart_dir(BACKTEST_RESULT_PATH)
    
    # List of tickers to analyze
    tickers = [
        "KRW-BTC",    # Bitcoin
        "KRW-ETH",    # Ethereum
        "KRW-XRP",    # Ripple
    ]
    
    if enable_telegram:
        async with Bot(token=os.getenv('TELEGRAM_BOT_TOKEN')) as bot:
            if enable_backtest:
                await send_telegram_message("🚀 Starting cryptocurrency backtesting...", enable_telegram, bot)
                
                # 백테스팅 실행
                for ticker in tickers:
                    await run_backtest(bot, ticker, strategy, period, initial_capital, enable_telegram)
                
                await send_telegram_message("✅ Backtesting completed!", enable_telegram, bot)
            else:
                await send_telegram_message("🚀 Starting cryptocurrency analysis...", enable_telegram, bot)
                
                # Analyze each ticker
                for ticker in tickers:
                    await analyze_ticker(bot, ticker, enable_telegram)
                
                await send_telegram_message("✅ Analysis completed!", enable_telegram, bot)
    else:
        # 백테스팅 모드일 경우
        if enable_backtest:
            print("🚀 Starting cryptocurrency backtesting...")
            
            # 백테스팅 실행
            for ticker in tickers:
                await run_backtest(None, ticker, strategy, period, initial_capital, enable_telegram)
            
            print("✅ Backtesting completed!")
        else:
            # Run without telegram notifications
            for ticker in tickers:
                await analyze_ticker(None, ticker, enable_telegram)

def main():
    # 명령줄 인자 파싱
    args = parse_args()
    
    # Run the async main function
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main() 