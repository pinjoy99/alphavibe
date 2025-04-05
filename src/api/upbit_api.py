import pyupbit
import pandas as pd
from typing import Optional, List, Dict, Any, Union
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
        interval (str): 시간 간격 (기본값: minute60)
        
    Returns:
        pd.DataFrame: OHLCV 데이터
    """
    # 기간 파싱
    from_date = parse_period_to_datetime(period_str)
    to_date = datetime.now()
    
    # 사용자가 지정한 interval을 우선 사용
    user_interval = interval
    
    # 기간에 따라 적절한 간격 자동 선택 (사용자가 지정한 interval이 없을 경우)
    match = re.match(r'(\d+)([dwmy])', period_str)
    if match and user_interval == "minute60":  # 사용자가 기본값을 사용한 경우에만 자동 조정
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
    else:
        # 사용자가 지정한 interval 사용
        interval = user_interval
    
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

def get_account_info() -> Optional[List[Dict[str, Any]]]:
    """
    업비트 계좌 정보 조회
    
    Returns:
        Optional[List[Dict[str, Any]]]: 계좌 잔고 목록 또는 실패 시 None
    """
    if not (UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY):
        print("계좌 정보를 조회하려면 API 키 설정이 필요합니다.")
        return None
    
    try:
        upbit = pyupbit.Upbit(UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY)
        return upbit.get_balances()
    except Exception as e:
        print(f"계좌 정보 조회 실패: {e}")
        return None

def get_order_history(ticker: Optional[str] = None, state: str = 'done', limit: int = 100) -> Optional[List[Dict[str, Any]]]:
    """
    주문 내역 조회 (개선된 버전)
    
    Parameters:
        ticker (str, optional): 종목 심볼 (없으면 전체 조회)
        state (str): 주문 상태 ('wait': 대기, 'done': 완료, 'cancel': 취소)
        limit (int): 최대 조회 건수
        
    Returns:
        Optional[List[Dict[str, Any]]]: 주문 내역 또는 실패 시 None
    """
    if not (UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY):
        print("주문 내역을 조회하려면 API 키 설정이 필요합니다.")
        return None
    
    try:
        upbit = pyupbit.Upbit(UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY)
        
        # ticker가 없는 경우 모든 주문 내역 조회 (모든 티커에 대해)
        if not ticker:
            # 전체 원화 마켓 티커 목록 조회
            tickers = get_ticker_list()
            
            # 결과를 합칠 리스트
            all_orders = []
            
            # 각 티커별로 주문 내역 조회 및 통합
            for t in tickers[:10]:  # 너무 많은 API 요청 방지를 위해 상위 10개만 조회
                try:
                    orders = upbit.get_order(t, state=state)
                    if orders:
                        all_orders.extend(orders)
                except Exception:
                    continue
            
            # 날짜순 정렬 (최신 주문 먼저)
            if all_orders:
                all_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                
                # 요청된 개수만큼 반환
                return all_orders[:limit]
            return []
            
        # 특정 티커의 주문 내역 조회
        return upbit.get_order(ticker, state=state, limit=limit)
    except Exception as e:
        print(f"주문 내역 조회 실패: {e}")
        return None

def get_current_price(ticker: Union[str, List[str]]) -> Union[float, Dict[str, float], None]:
    """
    현재가 조회 (개선된 버전)
    
    Parameters:
        ticker (str or List[str]): 종목 심볼 또는 심볼 리스트 (예: "KRW-BTC" 또는 ["KRW-BTC", "KRW-ETH"])
        
    Returns:
        float, Dict[str, float], or None: 현재가 또는 실패 시 None
    """
    try:
        price = pyupbit.get_current_price(ticker)
        
        # 딕셔너리인 경우 (여러 티커 요청 시)
        if isinstance(price, dict):
            # 값이 0인 항목 제거
            return {k: v for k, v in price.items() if v > 0}
        
        # 단일 값인 경우
        elif isinstance(price, (int, float)):
            return price if price > 0 else None
            
        return None
    except Exception as e:
        print(f"현재가 조회 실패: {e}")
        return None

def get_ticker_list() -> List[str]:
    """
    원화 마켓의 티커 목록 조회
    
    Returns:
        List[str]: 원화 마켓 티커 목록
    """
    try:
        tickers = pyupbit.get_tickers(fiat="KRW")
        return tickers
    except Exception as e:
        print(f"티커 목록 조회 실패: {e}")
        return [] 