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

# ----------------------
# 백테스팅 관련 함수들
# ----------------------

def parse_period_to_datetime(period_str: str) -> datetime:
    """
    기간 문자열을 datetime 객체로 변환
    
    Parameters:
        period_str (str): 기간 문자열 (예: 1d, 3d, 1w, 1m, 3m, 6m, 1y)
        
    Returns:
        datetime: 현재 시간에서 기간을 뺀 datetime 객체
    """
    now = datetime.now()
    
    # 숫자와 단위 분리
    import re
    match = re.match(r'(\d+)([dwmy])', period_str)
    if not match:
        raise ValueError(f"Invalid period format: {period_str}. Use format like 1d, 3d, 1w, 1m, 3m, 6m, 1y")
    
    value, unit = int(match.group(1)), match.group(2)
    
    if unit == 'd':
        return now - timedelta(days=value)
    elif unit == 'w':
        return now - timedelta(weeks=value)
    elif unit == 'm':
        return now - timedelta(days=value * 30)
    elif unit == 'y':
        return now - timedelta(days=value * 365)
    else:
        raise ValueError(f"Invalid period unit: {unit}")

def get_backtest_data(ticker: str, period_str: str, interval: str = "minute60") -> pd.DataFrame:
    """
    백테스팅용 데이터 조회
    
    Parameters:
        ticker (str): 종목 심볼 (예: "KRW-BTC")
        period_str (str): 기간 문자열 (예: 1d, 3d, 1w, 1m, 3m, 6m, 1y)
        interval (str): 시간 간격
        
    Returns:
        pd.DataFrame: OHLCV 데이터
    """
    # 기간 파싱
    from_date = parse_period_to_datetime(period_str)
    
    # 데이터 조회
    df = pyupbit.get_ohlcv_from(ticker, interval=interval, fromDatetime=from_date)
    
    return df

def apply_sma_strategy(df: pd.DataFrame, short_window: int = 5, long_window: int = 20) -> pd.DataFrame:
    """
    단순 이동평균선(SMA) 전략 적용
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터
        short_window (int): 단기 이동평균선 기간
        long_window (int): 장기 이동평균선 기간
        
    Returns:
        pd.DataFrame: 신호가 추가된 데이터프레임
    """
    # 단기/장기 이동평균선 계산
    df['short_ma'] = df['close'].rolling(window=short_window).mean()
    df['long_ma'] = df['close'].rolling(window=long_window).mean()
    
    # 신호 생성
    df['signal'] = 0
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1  # 매수 신호
    df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1  # 매도 신호
    
    # 신호 변화 감지
    df['position'] = df['signal'].diff()
    
    return df

def apply_bollinger_bands_strategy(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """
    볼린저 밴드 전략 적용
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터
        window (int): 이동평균선 기간
        num_std (float): 표준편차 배수
        
    Returns:
        pd.DataFrame: 신호가 추가된 데이터프레임
    """
    # 볼린저 밴드 계산
    df['ma'] = df['close'].rolling(window=window).mean()
    df['std'] = df['close'].rolling(window=window).std()
    df['upper_band'] = df['ma'] + (df['std'] * num_std)
    df['lower_band'] = df['ma'] - (df['std'] * num_std)
    
    # 신호 생성
    df['signal'] = 0
    df.loc[df['close'] < df['lower_band'], 'signal'] = 1  # 매수 신호 (하단 밴드 아래로)
    df.loc[df['close'] > df['upper_band'], 'signal'] = -1  # 매도 신호 (상단 밴드 위로)
    
    # 신호 변화 감지
    df['position'] = df['signal'].diff()
    
    return df

def apply_macd_strategy(df: pd.DataFrame, short_window: int = 12, long_window: int = 26, signal_window: int = 9) -> pd.DataFrame:
    """
    MACD 전략 적용
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터
        short_window (int): 단기 EMA 기간
        long_window (int): 장기 EMA 기간
        signal_window (int): 시그널 EMA 기간
        
    Returns:
        pd.DataFrame: 신호가 추가된 데이터프레임
    """
    # MACD 계산
    df['short_ema'] = df['close'].ewm(span=short_window, adjust=False).mean()
    df['long_ema'] = df['close'].ewm(span=long_window, adjust=False).mean()
    df['macd'] = df['short_ema'] - df['long_ema']
    df['signal_line'] = df['macd'].ewm(span=signal_window, adjust=False).mean()
    df['histogram'] = df['macd'] - df['signal_line']
    
    # 신호 생성
    df['signal'] = 0
    df.loc[df['macd'] > df['signal_line'], 'signal'] = 1  # 매수 신호
    df.loc[df['macd'] < df['signal_line'], 'signal'] = -1  # 매도 신호
    
    # 신호 변화 감지
    df['position'] = df['signal'].diff()
    
    return df

def backtest_strategy(df: pd.DataFrame, initial_capital: float = 1000000.0) -> Dict[str, Any]:
    """
    전략 백테스팅 실행
    
    Parameters:
        df (pd.DataFrame): 신호가 포함된 데이터프레임
        initial_capital (float): 초기 자본금
        
    Returns:
        dict: 백테스팅 결과 정보
    """
    # 결과를 저장할 데이터프레임 생성
    backtest_results = df.copy()
    
    # 포지션과 현금, 자산 초기화
    backtest_results['position_value'] = 0.0
    backtest_results['cash'] = initial_capital
    backtest_results['asset_value'] = initial_capital
    backtest_results['coin_amount'] = 0.0
    
    # 백테스팅 실행
    for i in range(1, len(backtest_results)):
        # 전날 정보
        prev_cash = backtest_results.loc[backtest_results.index[i-1], 'cash']
        prev_coin_amount = backtest_results.loc[backtest_results.index[i-1], 'coin_amount']
        
        # 당일 가격
        price = backtest_results.loc[backtest_results.index[i], 'close']
        
        # 신호 변화 확인
        position_change = backtest_results.loc[backtest_results.index[i], 'position']
        
        # 새로운 매수 신호
        if position_change == 1:
            # 보유 현금으로 코인 구매
            new_coin_amount = prev_cash / price
            backtest_results.loc[backtest_results.index[i], 'coin_amount'] = new_coin_amount
            backtest_results.loc[backtest_results.index[i], 'cash'] = 0
        
        # 새로운 매도 신호
        elif position_change == -2:  # 1에서 -1로 변할 때
            # 보유 코인 모두 판매
            new_cash = prev_coin_amount * price
            backtest_results.loc[backtest_results.index[i], 'coin_amount'] = 0
            backtest_results.loc[backtest_results.index[i], 'cash'] = new_cash
        
        # 신호 없음 (포지션 유지)
        else:
            backtest_results.loc[backtest_results.index[i], 'coin_amount'] = prev_coin_amount
            backtest_results.loc[backtest_results.index[i], 'cash'] = prev_cash
        
        # 포지션 가치 및 총 자산 가치 계산
        coin_value = backtest_results.loc[backtest_results.index[i], 'coin_amount'] * price
        backtest_results.loc[backtest_results.index[i], 'position_value'] = coin_value
        backtest_results.loc[backtest_results.index[i], 'asset_value'] = coin_value + backtest_results.loc[backtest_results.index[i], 'cash']
    
    # 결과 요약
    start_date = backtest_results.index[0]
    end_date = backtest_results.index[-1]
    total_days = (end_date - start_date).days
    
    final_value = backtest_results['asset_value'].iloc[-1]
    initial_value = backtest_results['asset_value'].iloc[0]
    total_return = (final_value - initial_value) / initial_value * 100
    
    # 연간 수익률 계산
    annual_return = (final_value / initial_value) ** (365 / total_days) - 1 if total_days > 0 else 0
    annual_return_pct = annual_return * 100
    
    # 최대 낙폭 계산
    backtest_results['drawdown'] = (backtest_results['asset_value'] / backtest_results['asset_value'].cummax() - 1) * 100
    max_drawdown = backtest_results['drawdown'].min()
    
    # 거래 횟수 계산
    trades = backtest_results[backtest_results['position'] != 0]
    trade_count = len(trades)
    
    result = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'total_days': total_days,
        'initial_capital': initial_value,
        'final_capital': final_value,
        'total_return_pct': total_return,
        'annual_return_pct': annual_return_pct,
        'max_drawdown_pct': max_drawdown,
        'trade_count': trade_count,
        'results_df': backtest_results
    }
    
    return result

def plot_backtest_results(ticker: str, results: Dict[str, Any]) -> str:
    """
    백테스팅 결과 시각화
    
    Parameters:
        ticker (str): 종목 심볼
        results (dict): 백테스팅 결과
        
    Returns:
        str: 저장된 차트 경로
    """
    results_df = results['results_df']
    
    # 2개의 그래프(가격+전략, 자산가치)를 포함한 차트 생성
    fig, axes = plt.subplots(2, 1, figsize=(12, 12), gridspec_kw={'height_ratios': [2, 1]})
    
    # 첫 번째 그래프: 가격 차트 + 전략 지표
    axes[0].plot(results_df.index, results_df['close'], label='Close Price', color='black', alpha=0.6)
    
    # 전략별 시각화 (short_ma와 long_ma 존재 확인)
    if 'short_ma' in results_df.columns and 'long_ma' in results_df.columns:
        # SMA 전략
        axes[0].plot(results_df.index, results_df['short_ma'], label=f"Short MA", color='blue')
        axes[0].plot(results_df.index, results_df['long_ma'], label=f"Long MA", color='red')
    elif 'upper_band' in results_df.columns and 'lower_band' in results_df.columns:
        # 볼린저 밴드 전략
        axes[0].plot(results_df.index, results_df['ma'], label='Moving Average', color='blue')
        axes[0].plot(results_df.index, results_df['upper_band'], label='Upper Band', color='red', linestyle='--')
        axes[0].plot(results_df.index, results_df['lower_band'], label='Lower Band', color='green', linestyle='--')
    elif 'macd' in results_df.columns and 'signal_line' in results_df.columns:
        # MACD 전략 (보조 축 추가)
        ax_macd = axes[0].twinx()
        ax_macd.plot(results_df.index, results_df['macd'], label='MACD', color='blue', alpha=0.7)
        ax_macd.plot(results_df.index, results_df['signal_line'], label='Signal Line', color='red', alpha=0.7)
        ax_macd.fill_between(results_df.index, results_df['histogram'], 0, 
                            where=(results_df['histogram'] > 0), color='green', alpha=0.3)
        ax_macd.fill_between(results_df.index, results_df['histogram'], 0, 
                            where=(results_df['histogram'] < 0), color='red', alpha=0.3)
        ax_macd.set_ylabel('MACD')
        ax_macd.legend(loc='upper right')
    
    # 매수/매도 신호 표시
    buy_signals = results_df[results_df['position'] == 1]
    sell_signals = results_df[results_df['position'] == -1]
    
    axes[0].scatter(buy_signals.index, buy_signals['close'], marker='^', color='green', s=100, label='Buy Signal')
    axes[0].scatter(sell_signals.index, sell_signals['close'], marker='v', color='red', s=100, label='Sell Signal')
    
    axes[0].set_title(f'{ticker} Price Chart and Signals')
    axes[0].set_ylabel('Price (KRW)')
    axes[0].legend()
    axes[0].grid(True)
    
    # 두 번째 그래프: 자산 가치 변화
    axes[1].plot(results_df.index, results_df['asset_value'], label='Total Asset Value', color='green')
    axes[1].plot(results_df.index, results_df['cash'], label='Cash', color='blue', linestyle='--', alpha=0.5)
    axes[1].plot(results_df.index, results_df['position_value'], label='Position Value', color='orange', linestyle='--', alpha=0.5)
    
    # 최대 낙폭 표시
    axes[1].fill_between(results_df.index, results_df['asset_value'], results_df['asset_value'].cummax(), 
                         where=(results_df['asset_value'] < results_df['asset_value'].cummax()), 
                         color='red', alpha=0.3, label='Drawdown')
    
    axes[1].set_title('Asset Value Change')
    axes[1].set_ylabel('Asset Value (KRW)')
    axes[1].set_xlabel('Date')
    axes[1].legend()
    axes[1].grid(True)
    
    # 전체 타이틀 설정
    total_return = results['total_return_pct']
    annual_return = results['annual_return_pct']
    max_drawdown = results['max_drawdown_pct']
    trade_count = results['trade_count']
    
    plt.suptitle(f'{ticker} Backtest Results ({results["start_date"]} ~ {results["end_date"]})\n'
                f'Total Return: {total_return:.2f}%, Annual Return: {annual_return:.2f}%, '
                f'Max Drawdown: {max_drawdown:.2f}%, Trades: {trade_count}',
                fontsize=14)
    
    plt.tight_layout()
    
    # 차트 저장
    os.makedirs(os.path.join(SCRIPT_DIR, BACKTEST_RESULT_PATH), exist_ok=True)
    save_path = os.path.join(SCRIPT_DIR, BACKTEST_RESULT_PATH, f'{ticker}_backtest_{datetime.now().strftime("%Y%m%d")}.png')
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    
    return save_path

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
        if strategy == "sma":
            df = apply_sma_strategy(df)
        elif strategy == "bb":
            df = apply_bollinger_bands_strategy(df)
        elif strategy == "macd":
            df = apply_macd_strategy(df)
        
        # 백테스팅 실행
        results = backtest_strategy(df, initial_capital)
        
        # 결과 출력
        print("\n백테스팅 결과:")
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

🔹 <b>전략:</b> {strategy.upper()}
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