import pyupbit
import pandas as pd
from typing import Optional
from datetime import datetime
from src.utils import (
    UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY, 
    DEFAULT_INTERVAL, DEFAULT_COUNT,
    parse_period_to_datetime
)
import re

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

def get_backtest_data(ticker: str, period_str: str, interval: str = "minute60") -> pd.DataFrame:
    """
    백테스팅용 데이터 조회
    
    Parameters:
        ticker (str): 종목 심볼 (예: "KRW-BTC")
        period_str (str): 기간 문자열 (예: 1d, 3d, 1w, 1m, 3m, 6m, 1y)
        interval (str): 시간 간격 (기본값: minute60, 기간에 따라 자동 조정 가능)
        
    Returns:
        pd.DataFrame: OHLCV 데이터
    """
    # 기간 파싱
    from_date = parse_period_to_datetime(period_str)
    to_date = datetime.now()
    
    # 기간에 따라 적절한 간격 자동 선택
    match = re.match(r'(\d+)([dwmy])', period_str)
    if match:
        value, unit = int(match.group(1)), match.group(2)
        
        # 6개월 이상인 경우 일봉 데이터 사용
        if (unit == 'y') or (unit == 'm' and value >= 6):
            interval = "day"
        # 3~6개월인 경우 4시간 데이터 사용
        elif (unit == 'm' and value >= 3) or (unit == 'w' and value >= 12):
            interval = "minute240"
        # 1~3개월인 경우 1시간 데이터 사용
        elif (unit == 'm' and value >= 1) or (unit == 'w' and value >= 4):
            interval = "minute60"
        # 그 이하는 기본값 사용 (minute60)
    
    print(f"데이터 조회 기간: {from_date.strftime('%Y-%m-%d')} ~ {to_date.strftime('%Y-%m-%d')} (간격: {interval})")
    
    # 데이터 조회
    try:
        # pyupbit.get_ohlcv_from은 toDatetime 매개변수를 지원하지 않음
        # 데이터를 먼저 가져온 후 날짜 범위로 필터링
        df = pyupbit.get_ohlcv_from(ticker, interval=interval, fromDatetime=from_date)
        
        # 가져온 데이터를 to_date 이하로 필터링
        if df is not None and not df.empty:
            df = df[df.index <= to_date]
            
            # 실제 조회된 데이터 기간 출력
            actual_from = df.index[0].strftime('%Y-%m-%d')
            actual_to = df.index[-1].strftime('%Y-%m-%d')
            print(f"실제 조회된 데이터 기간: {actual_from} ~ {actual_to} (총 {len(df)}개 데이터)")
        else:
            print("데이터 없음")
            df = pd.DataFrame()
            
    except Exception as e:
        print(f"데이터 조회 오류: {e}")
        df = pd.DataFrame()
    
    return df 