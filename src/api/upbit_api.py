import pyupbit
import pandas as pd
from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import datetime, timedelta
from src.utils import (
    UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY, 
    DEFAULT_INTERVAL, DEFAULT_COUNT,
    parse_period_to_datetime
)
import re
import logging

logger = logging.getLogger(__name__)

def parse_period_to_datetime(period: str) -> Tuple[datetime, datetime]:
    """
    기간 문자열을 시작/종료 datetime으로 변환
    
    Args:
        period: 기간 문자열 (예: '1d', '3d', '1w', '1m', '3m', '6m', '1y')
    
    Returns:
        (시작일시, 종료일시) 튜플
    """
    end_date = datetime.now()
    
    # 기간에 따른 시작일 계산
    period_map = {
        'd': 'days',
        'w': 'weeks',
        'm': 'months',
        'y': 'years'
    }
    
    try:
        amount = int(period[:-1])
        unit = period[-1].lower()
        
        if unit not in period_map:
            raise ValueError(f"지원하지 않는 기간 단위: {unit}")
        
        if unit == 'm':
            start_date = end_date - pd.DateOffset(months=amount)
        elif unit == 'y':
            start_date = end_date - pd.DateOffset(years=amount)
        else:
            delta = timedelta(**{period_map[unit]: amount})
            start_date = end_date - delta
            
        return start_date, end_date
        
    except (ValueError, IndexError) as e:
        logger.error(f"기간 파싱 중 에러 발생: {str(e)}")
        raise ValueError(f"잘못된 기간 형식: {period}")

def get_historical_data(ticker: str, period: str, interval: str = 'minute60') -> Optional[pd.DataFrame]:
    """
    업비트에서 히스토리컬 데이터 조회
    
    Args:
        ticker: 코인 심볼 (예: 'BTC')
        period: 기간 (예: '1d', '3d', '1w', '1m', '3m', '6m', '1y')
        interval: 데이터 간격 (예: 'minute1', 'minute3', 'minute5', 'minute15', 'minute60', 'day')
    
    Returns:
        OHLCV 데이터프레임 또는 None (에러 발생 시)
    """
    try:
        logger.info(f"데이터 조회 시작: {ticker}, 기간: {period}, 간격: {interval}")
        
        # 마켓 코드 생성 (KRW-BTC 형식)
        market = f"KRW-{ticker}"
        
        # 시작/종료일 계산
        start_date, end_date = parse_period_to_datetime(period)
        
        # 데이터 조회
        if interval == 'day':
            df = pyupbit.get_ohlcv(market, interval='day', to=end_date, count=500)
        else:
            # interval이 'minute60'와 같은 형식일 경우
            minutes = int(interval.replace('minute', ''))
            df = pyupbit.get_ohlcv(market, interval=interval, to=end_date, count=500)
        
        if df is None or df.empty:
            logger.warning(f"데이터가 없습니다: {ticker}")
            return None
            
        # 기간에 맞게 데이터 필터링
        df = df[df.index >= start_date]
        
        # 컬럼명 변경
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Value']
        
        logger.info(f"데이터 조회 완료: {len(df)} 개 데이터 포인트")
        
        return df
        
    except Exception as e:
        logger.error(f"데이터 조회 중 에러 발생: {str(e)}")
        return None

def get_backtest_data(ticker: str, period: str, interval: str = 'minute60') -> Optional[pd.DataFrame]:
    """
    백테스팅용 데이터 조회 및 전처리 (캐싱 적용)
    
    Args:
        ticker: 코인 심볼
        period: 기간
        interval: 데이터 간격
    
    Returns:
        전처리된 OHLCV 데이터프레임 또는 None
    """
    try:
        from src.utils.cache_manager import CacheManager
        from datetime import timedelta
        
        # 캐시 매니저 초기화
        cache_manager = CacheManager()
        
        # 캐시 키 구성
        cache_key = {
            "ticker": ticker,
            "period": period,
            "interval": interval,
            "type": "backtest_data"
        }
        
        # 캐시에서 데이터 로드 시도 (최대 1시간 유효)
        cached_data = cache_manager.load_from_cache(
            cache_key,
            extension="parquet",
            max_age=timedelta(hours=1)
        )
        
        if cached_data is not None:
            logger.info(f"캐시에서 데이터 로드: {ticker}")
            return cached_data
            
        # 데이터 조회
        df = get_historical_data(ticker, period, interval)
        if df is None:
            return None
            
        # 필요한 컬럼만 선택
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        # 결측치 처리
        df = df.dropna()
        
        # 캐시에 저장
        cache_manager.save_to_cache(
            df,
            cache_key,
            extension="parquet",
            max_age=timedelta(hours=1)
        )
        
        return df
        
    except Exception as e:
        logger.error(f"백테스트 데이터 준비 중 에러 발생: {str(e)}")
        return None

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