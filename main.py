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
from typing import Optional, Dict, Any
import numpy as np
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import koreanize_matplotlib  # 한글 폰트 적용
from src.api.upbit_api import get_historical_data, parse_period_to_datetime, get_backtest_data
from src.backtest import (
    apply_sma_strategy,
    apply_bollinger_bands_strategy,
    apply_macd_strategy,
    backtest_strategy,
    plot_backtest_results
)

# 명령줄 인자 파싱
def parse_args():
    parser = argparse.ArgumentParser(description="암호화폐 가격 분석")
    parser.add_argument("--telegram", "-t", action="store_true", help="텔레그램 알림 활성화")
    parser.add_argument("--backtest", "-b", action="store_true", help="백테스팅 모드 활성화")
    parser.add_argument("--strategy", "-s", choices=["sma", "bb", "macd"], default="sma", help="백테스팅 전략 선택 (기본값: sma)")
    parser.add_argument("--period", "-p", type=str, default="3m", help="백테스팅 기간 (예: 1d, 3d, 1w, 1m, 3m, 6m, 1y)")
    parser.add_argument("--invest", "-i", type=float, default=1000000, help="백테스팅 초기 투자금액 (원화)")
    return parser.parse_args()

# Load environment variables
load_dotenv()

# Get settings from environment variables
CHART_SAVE_PATH = os.getenv('CHART_SAVE_PATH', 'charts')
DEFAULT_INTERVAL = os.getenv('DEFAULT_INTERVAL', 'day')
DEFAULT_COUNT = int(os.getenv('DEFAULT_COUNT', '100'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# API key settings
UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')

# Telegram settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 백테스팅 설정
BACKTEST_DATA_PATH = os.getenv('BACKTEST_DATA_PATH', 'backtest_data')
BACKTEST_RESULT_PATH = os.getenv('BACKTEST_RESULT_PATH', 'backtest_results')

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

async def send_telegram_message(bot: Bot, message: str, enable_telegram: bool) -> None:
    """Send message to Telegram"""
    if not enable_telegram:
        return
    
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
    except Exception as e:
        print(f"Failed to send telegram message: {e}")

async def send_telegram_chart(bot: Bot, chart_path: str, caption: str, enable_telegram: bool) -> None:
    """Send chart image to Telegram"""
    if not enable_telegram:
        return
    
    try:
        with open(chart_path, 'rb') as chart:
            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=chart,
                caption=caption,
                parse_mode='HTML'
            )
    except Exception as e:
        print(f"Failed to send telegram chart: {e}")

# ----------------------
# 백테스팅 실행 함수
# ----------------------

async def run_backtest(bot: Bot, ticker: str, strategy: str, period: str, initial_capital: float, enable_telegram: bool) -> None:
    """
    백테스팅 실행
    
    Parameters:
        bot (Bot): 텔레그램 봇 인스턴스
        ticker (str): 종목 심볼
        strategy (str): 전략 이름
        period (str): 백테스팅 기간
        initial_capital (float): 초기 투자금액
        enable_telegram (bool): 텔레그램 알림 활성화 여부
    """
    print(f"\n백테스팅 시작: {ticker} (전략: {strategy}, 기간: {period})")
    
    if enable_telegram:
        await send_telegram_message(bot, f"🔍 백테스팅 시작: {ticker} (전략: {strategy}, 기간: {period})", enable_telegram)
    
    # 백테스팅 데이터 조회
    interval = "minute60"  # 1시간 간격 데이터 사용
    df = get_backtest_data(ticker, period, interval)
    
    if df is not None and not df.empty:
        # 전략 적용
        strategy_params = {}
        if strategy == "sma":
            # SMA 파라미터 최적화 - 더 긴 이동평균선 기간 사용
            short_window = 10  # 이전: 5
            long_window = 30   # 이전: 20
            strategy_params = {"short_window": short_window, "long_window": long_window}
            df = apply_sma_strategy(df, short_window=short_window, long_window=long_window)
        elif strategy == "bb":
            # 볼린저 밴드 파라미터
            window = 20
            std_dev = 2.0
            strategy_params = {"window": window, "std_dev": std_dev}
            df = apply_bollinger_bands_strategy(df, window=window, num_std=std_dev)
        elif strategy == "macd":
            # MACD 파라미터
            short_window = 12
            long_window = 26
            signal_window = 9
            strategy_params = {"short_window": short_window, "long_window": long_window, "signal_window": signal_window}
            df = apply_macd_strategy(df, short_window=short_window, long_window=long_window, signal_window=signal_window)
        
        # 백테스팅 실행
        results = backtest_strategy(df, initial_capital)
        
        # 결과에 전략 정보 추가
        results['strategy'] = strategy.upper()
        results['strategy_params'] = strategy_params
        
        # 결과 출력
        print("\n백테스팅 결과:")
        print(f"전략: {strategy.upper()}")
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
            result_message = f"""
📊 <b>{ticker} 백테스팅 결과</b>

🔹 <b>전략:</b> {strategy.upper()} (단기: {strategy_params.get('short_window', '-')}, 장기: {strategy_params.get('long_window', '-')})
📅 <b>기간:</b> {results['start_date']} ~ {results['end_date']} ({results['total_days']}일)
💰 <b>초기 자본금:</b> {results['initial_capital']:,.0f} KRW
💰 <b>최종 자본금:</b> {results['final_capital']:,.0f} KRW
📈 <b>총 수익률:</b> {results['total_return_pct']:.2f}%
📈 <b>연간 수익률:</b> {results['annual_return_pct']:.2f}%
📉 <b>최대 낙폭:</b> {results['max_drawdown_pct']:.2f}%
🔄 <b>거래 횟수:</b> {results['trade_count']}
"""
            # 차트 전송
            await send_telegram_chart(bot, chart_path, result_message, enable_telegram)
    else:
        error_message = f"백테스팅 데이터 조회 실패: {ticker}"
        print(error_message)
        if enable_telegram:
            await send_telegram_message(bot, f"❌ {error_message}", enable_telegram)

def plot_price_chart(df, ticker):
    """
    Plot price chart
    
    Parameters:
        df (DataFrame): OHLCV data
        ticker (str): Ticker symbol
    """
    plt.figure(figsize=(12, 6))
    
    # Closing price graph
    plt.plot(df.index, df['close'], label='Close', color='blue')
    
    # Moving average (20 days)
    ma20 = df['close'].rolling(window=20).mean()
    plt.plot(df.index, ma20, label='20-day MA', color='red')
    
    plt.title(f'{ticker} Price Chart')
    plt.xlabel('Date')
    plt.ylabel('Price (KRW)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    
    # Save chart
    save_path = os.path.join(SCRIPT_DIR, CHART_SAVE_PATH, f'{ticker}_chart.png')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    
    return save_path

def format_stats_message(ticker: str, stats: Dict[str, Any]) -> str:
    """Format statistics message for Telegram"""
    return f"""
📊 <b>{ticker} Analysis Results</b>

📅 Period: {stats['start_date']} ~ {stats['end_date']}
💰 Highest: {stats['highest_price']:,} KRW
💰 Lowest: {stats['lowest_price']:,} KRW
📈 Volume: {stats['volume']:,}
"""

async def analyze_ticker(bot: Bot, ticker: str, enable_telegram: bool) -> None:
    """Analyze single ticker and send results to Telegram"""
    print(f"\nAnalyzing {ticker}...")
    
    if enable_telegram:
        await send_telegram_message(bot, f"🔍 Starting analysis for {ticker}...", enable_telegram)
    
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
        
        # Create and save chart
        chart_path = plot_price_chart(df, ticker)
        print(f"Chart saved: {os.path.join(CHART_SAVE_PATH, f'{ticker}_chart.png')}")
        
        # Send to Telegram if enabled
        if enable_telegram:
            stats_message = format_stats_message(ticker, stats)
            await send_telegram_chart(bot, chart_path, stats_message, enable_telegram)
    else:
        error_message = f"Failed to fetch data for {ticker}"
        print(error_message)
        if enable_telegram:
            await send_telegram_message(bot, f"❌ {error_message}", enable_telegram)

async def main_async(args):
    # 명령줄 인자 추출
    enable_telegram = args.telegram
    enable_backtest = args.backtest
    strategy = args.strategy
    period = args.period
    initial_capital = args.invest
    
    # Create directory for saving charts
    charts_dir = os.path.join(SCRIPT_DIR, CHART_SAVE_PATH)
    os.makedirs(charts_dir, exist_ok=True)
    
    # 백테스팅 결과 디렉토리 생성
    if enable_backtest:
        backtest_results_dir = os.path.join(SCRIPT_DIR, BACKTEST_RESULT_PATH)
        os.makedirs(backtest_results_dir, exist_ok=True)
    
    # List of tickers to analyze
    tickers = [
        "KRW-BTC",    # Bitcoin
        "KRW-ETH",    # Ethereum
        "KRW-XRP",    # Ripple
    ]
    
    if enable_telegram:
        async with Bot(token=TELEGRAM_BOT_TOKEN) as bot:
            if enable_backtest:
                await send_telegram_message(bot, "🚀 Starting cryptocurrency backtesting...", enable_telegram)
                
                # 백테스팅 실행
                for ticker in tickers:
                    await run_backtest(bot, ticker, strategy, period, initial_capital, enable_telegram)
                
                await send_telegram_message(bot, "✅ Backtesting completed!", enable_telegram)
            else:
                await send_telegram_message(bot, "🚀 Starting cryptocurrency analysis...", enable_telegram)
                
                # Analyze each ticker
                for ticker in tickers:
                    await analyze_ticker(bot, ticker, enable_telegram)
                
                await send_telegram_message(bot, "✅ Analysis completed!", enable_telegram)
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