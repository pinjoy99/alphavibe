"""
차트 유틸리티 모듈

시각화에 사용되는 공통 유틸리티 함수를 제공합니다.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
from typing import Tuple, List, Optional, Dict, Any, Union

from src.utils.file_utils import ensure_directory
from src.utils.config import CHART_SAVE_PATH

def setup_chart_dir(chart_dir: str = CHART_SAVE_PATH) -> str:
    """
    차트 저장 디렉토리 설정 및 생성
    
    Parameters:
        chart_dir (str): 차트 저장 경로 (기본값: CHART_SAVE_PATH)
        
    Returns:
        str: 생성된 차트 디렉토리 경로
    """
    # 디렉토리 생성 및 경로 반환
    return ensure_directory(chart_dir)

def format_date_axis(ax, rotate_labels: bool = False, hide_labels: bool = False, date_format: str = '%m/%d'):
    """
    날짜 축 포맷 설정 (개선된 버전)
    
    Parameters:
        ax: matplotlib 축 객체
        rotate_labels (bool): 라벨을 회전할지 여부 (기본값: False - 회전 안 함)
        hide_labels (bool): 라벨을 숨길지 여부
        date_format (str): 날짜 표시 형식
    """
    # 날짜 포맷터 설정
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    
    # 데이터에 따라 로케이터 설정
    if len(ax.get_xticks()) > 0:
        data_range = ax.get_xlim()[1] - ax.get_xlim()[0]
        if data_range > 180:  # 6개월 이상
            ax.xaxis.set_major_locator(mdates.MonthLocator())
        elif data_range > 60:  # 2개월 이상
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=15))  # 15일 간격
        elif data_range > 30:  # 1개월 이상
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))  # 1주 간격
        else:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, int(data_range // 10))))
    
    # 라벨 회전 설정
    if rotate_labels:
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    else:
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center')
    
    # 라벨 숨김 처리
    if hide_labels:
        plt.setp(ax.get_xticklabels(), visible=False)
    
    # 그리드 설정
    ax.grid(True, alpha=0.2)  # 그리드 투명도 감소

def format_price_axis(ax, currency_symbol: str = "KRW"):
    """
    가격 축 포맷 설정
    
    Parameters:
        ax: matplotlib 축 객체
        currency_symbol: 통화 기호
    """
    # 천 단위 콤마 포맷터 설정
    if currency_symbol:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, loc: "{:,.0f} {}".format(x, currency_symbol) if x >= 1000000 
            else "{:,.0f}".format(x)))
    else:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, loc: "{:,.0f}".format(x)))
    
    # 그리드 설정
    ax.grid(True, alpha=0.3)

def save_chart(fig, file_name, chart_dir=CHART_SAVE_PATH, dpi=150) -> str:
    """
    차트 저장
    
    Parameters:
        fig: matplotlib 그림 객체
        file_name: 파일명
        chart_dir: 차트 저장 디렉토리
        dpi: 해상도
        
    Returns:
        str: 저장된 파일의 전체 경로
    """
    # 디렉토리 확인 및 생성
    chart_path = ensure_directory(chart_dir)
    
    # 파일 전체 경로
    full_path = os.path.join(chart_path, file_name)
    
    # 그림 저장
    fig.savefig(full_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    return full_path

def generate_filename(ticker: str, interval: str = "day", period: str = "1m", 
                     suffix: str = "", strategy: str = "", 
                     initial_capital: float = None, **kwargs) -> str:
    """
    차트 파일명 생성
    
    Parameters:
        ticker: 티커 심볼
        interval: 간격 (day, hour, minute)
        period: 기간 (1d, 5d, 1m, 3m, 6m, 1y)
        suffix: 파일명 접미사
        strategy: 전략 이름 (백테스팅에만 사용)
        initial_capital: 초기 자본금 (백테스팅에만 사용)
        **kwargs: 추가 매개변수
        
    Returns:
        str: 생성된 파일명
    """
    # 현재 시간
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 접미사가 있으면 언더스코어 추가
    suffix = f"_{suffix}" if suffix else ""
    
    # 전략 이름이 있으면 추가
    strategy_str = f"_{strategy}" if strategy else ""
    
    # 초기 자본금이 있으면 추가 (단위: 만원)
    capital_str = f"_{int(initial_capital/10000)}만원" if initial_capital else ""
    
    # 파일명 생성 - period 값을 그대로 사용
    filename = f"{ticker}_{interval}_{period}{strategy_str}{capital_str}{suffix}_{timestamp}.png"
    
    return filename

def detect_chart_type(df: pd.DataFrame) -> str:
    """
    데이터프레임의 컬럼을 기반으로 차트 타입 감지
    
    Parameters:
        df: 데이터프레임
        
    Returns:
        str: 차트 타입 ('candlestick', 'ohlc', 'line')
    """
    required_cols = {
        'candlestick': ['Open', 'High', 'Low', 'Close'],
        'ohlc': ['Open', 'High', 'Low', 'Close'],
        'line': ['Close']
    }
    
    # 대문자 컬럼명 확인
    if all(col in df.columns for col in required_cols['candlestick']):
        return 'candlestick'
    
    # 소문자 컬럼명 확인
    if all(col.lower() in [c.lower() for c in df.columns] for col in required_cols['candlestick']):
        return 'candlestick'
    
    # 종가만 있으면 라인 차트
    if 'Close' in df.columns or 'close' in df.columns:
        return 'line'
    
    # 기본값
    return 'line' 