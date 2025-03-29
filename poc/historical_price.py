import pyupbit
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from telegram import Bot
import asyncio
from typing import Optional, Dict, Any

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
ENABLE_TELEGRAM = os.getenv('ENABLE_TELEGRAM', 'false').lower() == 'true'

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

async def send_telegram_message(bot: Bot, message: str) -> None:
    """Send message to Telegram"""
    if not ENABLE_TELEGRAM:
        return
    
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
    except Exception as e:
        print(f"Failed to send telegram message: {e}")

async def send_telegram_chart(bot: Bot, chart_path: str, caption: str) -> None:
    """Send chart image to Telegram"""
    if not ENABLE_TELEGRAM:
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

def get_historical_data(ticker, interval=None, count=None):
    """
    Get historical price data
    
    Parameters:
        ticker (str): Ticker symbol (e.g., "KRW-BTC", "KRW-ETH")
        interval (str): Time interval ("day", "minute1", "minute3", "minute5", "minute10", "minute15", "minute30", "minute60", "minute240", "week", "month")
        count (int): Number of data points to retrieve
    """
    interval = interval or DEFAULT_INTERVAL
    count = count or DEFAULT_COUNT
    
    # Use authenticated client if API keys are set
    if UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY:
        upbit = pyupbit.Upbit(UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY)
        df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
    else:
        df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
    
    return df

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

async def analyze_ticker(bot: Bot, ticker: str) -> None:
    """Analyze single ticker and send results to Telegram"""
    print(f"\nAnalyzing {ticker}...")
    
    if ENABLE_TELEGRAM:
        await send_telegram_message(bot, f"🔍 Starting analysis for {ticker}...")
    
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
        if ENABLE_TELEGRAM:
            stats_message = format_stats_message(ticker, stats)
            await send_telegram_chart(bot, chart_path, stats_message)
    else:
        error_message = f"Failed to fetch data for {ticker}"
        print(error_message)
        if ENABLE_TELEGRAM:
            await send_telegram_message(bot, f"❌ {error_message}")

async def main_async():
    # Create directory for saving charts
    charts_dir = os.path.join(SCRIPT_DIR, CHART_SAVE_PATH)
    os.makedirs(charts_dir, exist_ok=True)
    
    # List of tickers to analyze
    tickers = [
        "KRW-BTC",    # Bitcoin
        "KRW-ETH",    # Ethereum
        "KRW-XRP",    # Ripple
    ]
    
    if ENABLE_TELEGRAM:
        async with Bot(token=TELEGRAM_BOT_TOKEN) as bot:
            await send_telegram_message(bot, "🚀 Starting cryptocurrency analysis...")
            
            # Analyze each ticker
            for ticker in tickers:
                await analyze_ticker(bot, ticker)
            
            await send_telegram_message(bot, "✅ Analysis completed!")
    else:
        # Run without telegram notifications
        for ticker in tickers:
            await analyze_ticker(None, ticker)

def main():
    # Run the async main function
    asyncio.run(main_async())

if __name__ == "__main__":
    main() 