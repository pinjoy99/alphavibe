"""
차트 저장 및 설정 관련 유틸리티 함수 모듈
"""
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import Optional, List, Tuple, Any

def setup_chart_dir(chart_dir: str) -> str:
    """
    차트 저장 디렉토리 생성 및 경로 반환
    
    Parameters:
        chart_dir (str): 차트 저장 디렉토리 경로
        
    Returns:
        str: 생성된 디렉토리 절대 경로
    """
    # 상대 경로를 절대 경로로 변환
    if not os.path.isabs(chart_dir):
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        chart_dir = os.path.join(script_dir, chart_dir)
    
    # 디렉토리가 없으면 생성
    os.makedirs(chart_dir, exist_ok=True)
    
    return chart_dir

def save_chart(fig: plt.Figure, file_name: str, chart_dir: str, dpi: int = 300) -> str:
    """
    차트를 파일로 저장하고 경로 반환
    
    Parameters:
        fig (plt.Figure): 저장할 matplotlib 피겨 객체
        file_name (str): 파일 이름
        chart_dir (str): 차트 저장 디렉토리 경로
        dpi (int): 해상도 (기본값: 300)
        
    Returns:
        str: 저장된 파일 경로
    """
    # 차트 디렉토리 생성
    full_dir = setup_chart_dir(chart_dir)
    
    # 파일 확장자 확인 및 추가
    if not file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.pdf')):
        file_name += '.png'
    
    # 전체 파일 경로
    file_path = os.path.join(full_dir, file_name)
    
    # 차트 저장
    fig.savefig(file_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    return file_path

def format_date_axis(ax: plt.Axes, rotation: int = 45, date_format: str = '%Y-%m-%d') -> None:
    """
    X축을 날짜 형식으로 포맷팅
    
    Parameters:
        ax (plt.Axes): 포맷팅할 matplotlib Axes 객체
        rotation (int): X축 레이블 회전 각도
        date_format (str): 날짜 포맷 지정 ('%Y-%m-%d' 등)
    """
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    ax.tick_params(axis='x', rotation=rotation)
    
    # 타임스케일의 범위에 따라 적절한 locator 선택
    date_range = ax.get_xlim()
    if date_range[1] - date_range[0] > 365:  # 1년 이상이면
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  # 2개월 간격
    elif date_range[1] - date_range[0] > 90:  # 3개월 이상이면
        ax.xaxis.set_major_locator(mdates.MonthLocator())  # 1개월 간격
    elif date_range[1] - date_range[0] > 30:  # 1개월 이상이면
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))  # 2주 간격
    else:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))  # 2일 간격

def format_price_axis(ax: plt.Axes, use_log_scale: bool = False) -> None:
    """
    Y축 가격 포맷팅 (로그 스케일 설정 포함)
    
    Parameters:
        ax (plt.Axes): 포맷팅할 matplotlib Axes 객체
        use_log_scale (bool): 로그 스케일 사용 여부
    """
    if use_log_scale:
        ax.set_yscale('log')
    
    # 천 단위 구분자 설정
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
def generate_filename(prefix: str, ticker: str, strategy: Optional[str] = None) -> str:
    """
    차트 파일 이름 생성
    
    Parameters:
        prefix (str): 파일 이름 접두사
        ticker (str): 종목 심볼
        strategy (Optional[str]): 전략 이름 (선택적)
        
    Returns:
        str: 생성된 파일 이름
    """
    current_date = datetime.now().strftime("%Y%m%d")
    
    if strategy:
        return f"{ticker}_{strategy}_{prefix}_{current_date}.png"
    else:
        return f"{ticker}_{prefix}_{current_date}.png"
