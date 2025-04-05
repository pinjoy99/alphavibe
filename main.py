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

def backtest_strategy(df: pd.DataFrame, initial_capital: float) -> Dict[str, Any]:
    """
    백테스팅 전략 실행
    
    Parameters:
        df (pd.DataFrame): 전략이 적용된 데이터프레임
        initial_capital (float): 초기 자본금
    
    Returns:
        Dict[str, Any]: 백테스팅 결과
    """
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
    백테스팅 결과 시각화
    
    Parameters:
        ticker (str): 종목 심볼
        results (Dict[str, Any]): 백테스팅 결과
    
    Returns:
        str: 저장된 차트 경로
    """
    # 결과 데이터 추출
    df = results['df']
    results_df = results['results_df']
    trade_history = results['trade_history']
    strategy = results.get('strategy', 'Unknown')
    strategy_params = results.get('strategy_params', {})
    
    # 전략 설명 텍스트 생성
    strategy_text = f"전략: {strategy}"
    if strategy == "SMA":
        short_window = strategy_params.get('short_window', '-')
        long_window = strategy_params.get('long_window', '-')
        strategy_text += f" (단기: {short_window}, 장기: {long_window})"
    elif strategy == "BB":
        window = strategy_params.get('window', '-')
        std_dev = strategy_params.get('std_dev', '-')
        strategy_text += f" (기간: {window}, 표준편차: {std_dev})"
    elif strategy == "MACD":
        short_window = strategy_params.get('short_window', '-')
        long_window = strategy_params.get('long_window', '-')
        signal_window = strategy_params.get('signal_window', '-')
        strategy_text += f" (단기: {short_window}, 장기: {long_window}, 시그널: {signal_window})"
    
    # 매수/매도 포인트 추출
    buy_points = [trade['date'] for trade in trade_history if trade['type'] == 'buy']
    sell_points = [trade['date'] for trade in trade_history if trade['type'] == 'sell']
    
    # 결과 지표
    total_return_pct = results['total_return_pct']
    annual_return_pct = results['annual_return_pct']
    max_drawdown_pct = results['max_drawdown_pct']
    trade_count = results['trade_count']
    initial_capital = results['initial_capital']
    final_capital = results['final_capital']
    
    # 그래프 설정
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 14))
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 1.5, 1.5, 1], hspace=0.15)
    
    # 1. 가격 차트 + 전략
    ax1 = plt.subplot(gs[0])
    
    # 가격 데이터 (로그 스케일)
    ax1.semilogy(df.index, df['close'], 'white', linewidth=1.5, label='가격')
    
    # 이동평균선 (가능한 경우)
    if 'short_ma' in df.columns and 'long_ma' in df.columns:
        ax1.semilogy(df.index, df['short_ma'], color='#FF9500', linewidth=1, label=f"단기 이동평균선")
        ax1.semilogy(df.index, df['long_ma'], color='#00BFFF', linewidth=1, label=f"장기 이동평균선")
    
    # 볼린저 밴드 (가능한 경우)
    if 'upper_band' in df.columns and 'lower_band' in df.columns:
        ax1.semilogy(df.index, df['upper_band'], color='#FF9500', linestyle='--', linewidth=0.8, label='상단 밴드')
        ax1.semilogy(df.index, df['lower_band'], color='#00BFFF', linestyle='--', linewidth=0.8, label='하단 밴드')
    
    # 거래 신호 샘플링 (신호가 많을 경우 일부만 표시)
    # 최대 20개만 표시 (가시성 확보)
    sample_factor = max(1, len(buy_points) // 20)
    sampled_buy_points = buy_points[::sample_factor]
    sampled_sell_points = sell_points[::sample_factor]
    
    # 매수/매도 신호 표시
    for bp in sampled_buy_points:
        if bp in df.index:
            ax1.scatter(bp, df.loc[bp, 'close'], color='#00FF00', s=100, marker='^', label='매수' if bp == sampled_buy_points[0] else "")
    
    for sp in sampled_sell_points:
        if sp in df.index:
            ax1.scatter(sp, df.loc[sp, 'close'], color='#FF0000', s=100, marker='v', label='매도' if sp == sampled_sell_points[0] else "")
    
    # 볼륨 표시 (볼륨 데이터가 있는 경우)
    if 'volume' in df.columns:
        volume_ax = ax1.twinx()
        volume_ax.bar(df.index, df['volume'], color='gray', alpha=0.3, width=0.8)
        volume_ax.set_ylim(0, df['volume'].max() * 5)
        volume_ax.set_ylabel('거래량', color='gray')
        volume_ax.tick_params(axis='y', colors='gray')
        volume_ax.grid(False)
    
    # 차트 설정
    ax1.set_title(f"{ticker} 가격 및 전략 신호\n{strategy_text}", fontsize=14, pad=10)
    ax1.set_ylabel('가격 (로그 스케일)', fontsize=12)
    ax1.grid(True, alpha=0.2)
    ax1.legend(loc='upper left', fontsize=10)
    
    # X축 날짜 포맷 설정 (년-월-일 형식)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. 자산 변화 그래프
    ax2 = plt.subplot(gs[1], sharex=ax1)
    
    # 로그 스케일 사용 여부 결정 (자산 변화가 크면 로그 스케일 사용)
    use_log_scale = results_df['asset'].max() / results_df['asset'].min() > 5
    
    if use_log_scale:
        ax2.semilogy(results_df.index, results_df['asset'], color='#00FF00', linewidth=1.5, label='자산 가치')
        ax2.set_ylabel('자산 가치 (로그)', fontsize=12)
    else:
        ax2.plot(results_df.index, results_df['asset'], color='#00FF00', linewidth=1.5, label='자산 가치')
        ax2.set_ylabel('자산 가치', fontsize=12)
    
    # 초기 자본금 표시 (기준선)
    ax2.axhline(y=initial_capital, color='white', linestyle='--', alpha=0.5, label='초기 자본금')
    
    # 차트 설정
    ax2.set_title("자산 가치 변화", fontsize=14, pad=10)
    ax2.grid(True, alpha=0.2)
    ax2.legend(loc='upper left', fontsize=10)
    
    # 3. 드로우다운 차트
    ax3 = plt.subplot(gs[2], sharex=ax1)
    ax3.fill_between(results_df.index, 0, results_df['drawdown'], color='#FF6347', alpha=0.5)
    ax3.plot(results_df.index, results_df['drawdown'], color='#FF6347', linewidth=1)
    
    # 차트 설정
    ax3.set_title("드로우다운 (%)", fontsize=14, pad=10)
    ax3.set_ylabel('드로우다운 (%)', fontsize=12)
    ax3.set_ylim(min(results_df['drawdown'].min() * 1.1, -10), 5)  # 최소값 이하로 여유 확보
    ax3.grid(True, alpha=0.2)
    
    # 4. 성과 지표 요약
    ax4 = plt.subplot(gs[3])
    ax4.axis('off')  # 축 숨기기
    
    # 요약 텍스트 생성
    summary_text = (
        f"전략 성과 요약 - {strategy}\n\n"
        f"초기 자본금: {initial_capital:,.0f} KRW | 최종 자본금: {final_capital:,.0f} KRW\n"
        f"총 수익률: {total_return_pct:.2f}% | 연간 수익률: {annual_return_pct:.2f}%\n"
        f"최대 낙폭: {max_drawdown_pct:.2f}% | 거래 횟수: {trade_count}\n"
        f"기간: {results['start_date']} ~ {results['end_date']} ({results['total_days']} 일)"
    )
    
    # 텍스트 색상 결정 (수익/손실에 따라)
    text_color = '#00FF00' if total_return_pct >= 0 else '#FF6347'
    
    # 요약 텍스트 표시
    ax4.text(0.5, 0.5, summary_text, horizontalalignment='center', verticalalignment='center',
             fontsize=12, color=text_color, transform=ax4.transAxes)
    
    # X축 데이터 포맷 설정 (중복 날짜 표시 방지)
    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.tick_params(axis='x', rotation=45)
    
    # 그래프 제목 설정
    plt.suptitle(f"{ticker} 백테스팅 결과 - {strategy} 전략 ({results['start_date']} ~ {results['end_date']})",
                 fontsize=16, y=0.98)
    
    # 그래프 저장
    os.makedirs("backtest_results", exist_ok=True)
    current_date = datetime.now().strftime("%Y%m%d")
    chart_path = f"backtest_results/{ticker}_{strategy}_backtest_{current_date}.png"
    plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='#333333')
    plt.close(fig)
    
    return chart_path

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

🔹 <b>전략:</b> {strategy.upper()} (단기: {short_window if strategy == 'sma' else '-'}, 장기: {long_window if strategy == 'sma' else '-'})
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