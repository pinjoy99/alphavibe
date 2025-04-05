"""
차트 저장 및 설정 관련 유틸리티 함수 모듈
"""
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import Optional, List, Tuple, Any
from src.utils import ensure_directory, CHART_DIR, generate_filename as utils_generate_filename

def setup_chart_dir(chart_dir: str) -> str:
    """
    차트 저장 디렉토리 생성 및 경로 반환 (하위 호환성 유지용)
    
    Parameters:
        chart_dir (str): 차트 저장 디렉토리 경로
        
    Returns:
        str: 생성된 디렉토리 절대 경로
    """
    return ensure_directory(chart_dir)

def save_chart(fig: plt.Figure, file_name: str, chart_dir: str = CHART_DIR, dpi: int = 300) -> str:
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
    full_dir = ensure_directory(chart_dir)
    
    # 파일 확장자 확인 및 추가
    if not file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.pdf')):
        file_name += '.png'
    
    # 전체 파일 경로
    file_path = os.path.join(full_dir, file_name)
    
    # 차트 저장
    fig.savefig(file_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    return file_path

def format_date_axis(ax: plt.Axes, rotation: int = 0, date_format: str = '%m/%d') -> None:
    """
    X축을 날짜 형식으로 포맷팅
    
    Parameters:
        ax (plt.Axes): 포맷팅할 matplotlib Axes 객체
        rotation (int): X축 레이블 회전 각도
        date_format (str): 날짜 포맷 지정 ('%Y-%m-%d' 등)
    """
    # 현재 날짜 기준으로 미래 날짜가 설정되지 않도록 제한
    today = datetime.now()
    
    # X축 레이블 포맷 설정
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    ax.tick_params(axis='x', rotation=rotation)
    
    # 날짜 범위 확인
    if hasattr(ax, 'get_xlim'):
        date_range = ax.get_xlim()
        
        # 타임스케일의 범위에 따라 적절한 locator 선택
        if date_range[1] - date_range[0] > 365:  # 1년 이상이면
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  # 2개월 간격
        elif date_range[1] - date_range[0] > 90:  # 3개월 이상이면
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))  # 1개월 간격
        elif date_range[1] - date_range[0] > 30:  # 1개월 이상이면
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))  # 2주 간격
        else:
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))  # 2일 간격
        
        # 시작 및 끝 날짜 설정을 위해 FixedLocator 추가
        # 데이터의 첫 날짜와 마지막 날짜를 포함하는 locator 생성
        try:
            # 현재 locator에서 틱 위치 가져오기
            current_ticks = ax.xaxis.get_major_locator()()
            
            # 데이터의 시작과 끝 날짜 추가
            first_date = date_range[0]
            last_date = date_range[1]
            
            # 모든 틱을 하나의 리스트로 결합
            all_ticks = sorted(list(set([first_date, last_date] + list(current_ticks))))
            
            # 새로운 locator 설정
            ax.xaxis.set_major_locator(mdates.FixedLocator(all_ticks))
        except Exception:
            # 오류 발생 시 기본 locator 사용
            pass

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

def generate_filename(ticker: str, strategy: Optional[str] = None, 
                    period: Optional[str] = None, initial_capital: Optional[float] = None,
                    interval: Optional[str] = None, prefix: Optional[str] = None) -> str:
    """
    차트 파일 이름 생성
    
    Parameters:
        ticker (str): 종목 심볼
        strategy (Optional[str]): 전략 이름 (선택적)
        period (Optional[str]): 백테스팅/분석 기간 (예: 1d, 3m, 6m, 1y)
        initial_capital (Optional[float]): 초기 투자금액
        interval (Optional[str]): 데이터 간격 (예: day, minute15, minute60)
        prefix (Optional[str]): 파일 이름 접두사 (선택적, 필요 없는 경우 무시됨)
        
    Returns:
        str: 생성된 파일 이름
    """
    # 날짜 형식 변경: YYYYMMDD -> YYMMDD
    current_date = datetime.now().strftime("%y%m%d")
    
    # 파일명 구성요소 준비
    components = [ticker]
    
    if strategy:
        components.append(strategy)
    
    if interval:
        # minute60 같은 형식을 m60 처럼 짧게 표현
        if interval.startswith('minute'):
            interval_short = f"m{interval[6:]}"
            components.append(interval_short)
        else:
            components.append(interval)
    
    if period:
        components.append(f"p{period}")
    
    if initial_capital:
        # 초기 자본금을 K(천), M(백만) 단위로 표현 (예: 1000000 -> 1M)
        if initial_capital >= 1000000:
            capital_str = f"{initial_capital/1000000:.1f}M".replace('.0', '')
        elif initial_capital >= 1000:
            capital_str = f"{initial_capital/1000:.1f}K".replace('.0', '')
        else:
            capital_str = f"{int(initial_capital)}"
        components.append(f"i{capital_str}")
    
    # prefix 추가 (선택적)
    if prefix:
        components.append(prefix)
        
    components.append(current_date)
    
    # 모든 구성요소를 언더스코어(_)로 연결
    return f"{'_'.join(components)}.png"

def set_chart_style(style='dark_background'):
    """
    차트 스타일 설정
    
    Parameters:
        style (str): 'dark_background', 'default', 'ggplot' 등 matplotlib 스타일
    """
    plt.style.use(style)
    # 폰트 크기 등 기본 설정
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
