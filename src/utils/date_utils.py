"""
날짜 및 시간 관련 유틸리티 함수 모듈
"""
from datetime import datetime, timedelta
import re
from typing import Optional
from dateutil.relativedelta import relativedelta

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
    match = re.match(r'(\d+)([dwmy])', period_str)
    if not match:
        raise ValueError(f"Invalid period format: {period_str}. Use format like 1d, 3d, 1w, 1m, 3m, 6m, 1y")
    
    value, unit = int(match.group(1)), match.group(2)
    
    if unit == 'd':
        return now - timedelta(days=value)
    elif unit == 'w':
        return now - timedelta(weeks=value)
    elif unit == 'm':
        # relativedelta를 사용하여 월 단위 계산
        return now - relativedelta(months=value)
    elif unit == 'y':
        # relativedelta를 사용하여 년 단위 계산
        return now - relativedelta(years=value)
    else:
        raise ValueError(f"Invalid period unit: {unit}")

def format_timestamp(dt: Optional[datetime] = None, 
                     format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    datetime 객체를 지정된 포맷으로 문자열 변환
    
    Parameters:
        dt (Optional[datetime]): 변환할 datetime 객체 (기본값: 현재 시간)
        format_str (str): 날짜/시간 포맷 문자열
        
    Returns:
        str: 포맷된 날짜/시간 문자열
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)

def get_date_range(days: int) -> tuple:
    """
    현재로부터 지정된 일수 이전의 날짜 범위 반환
    
    Parameters:
        days (int): 이전 일수
        
    Returns:
        tuple: (시작 날짜, 종료 날짜) - datetime 객체
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date 