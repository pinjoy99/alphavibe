import pyupbit
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import os

# API key settings
UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')

# Default settings
DEFAULT_INTERVAL = os.getenv('DEFAULT_INTERVAL', 'day')
DEFAULT_COUNT = int(os.getenv('DEFAULT_COUNT', '100'))

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