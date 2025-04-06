"""
시각화 내부 헬퍼 모듈

시각화 모듈 내부에서만 사용되는 유틸리티 함수를 제공합니다.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Any, Union

def prepare_ohlcv_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터프레임을 시각화에 사용할 수 있도록 준비
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        
    Returns:
        pd.DataFrame: 시각화용으로 처리된 데이터프레임
    """
    # 복사본 생성
    df = df.copy()
    
    # 컬럼명 표준화 (대소문자 무관하게 처리)
    column_mapping = {
        'open': 'open', 'Open': 'open',
        'high': 'high', 'High': 'high',
        'low': 'low', 'Low': 'low',
        'close': 'close', 'Close': 'close',
        'volume': 'volume', 'Volume': 'volume'
    }
    
    # 컬럼명 변경
    for col in df.columns:
        if col in column_mapping:
            df.rename(columns={col: column_mapping[col]}, inplace=True)
    
    # 날짜 인덱스 확인 및 변환
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'date' in df.columns:
            df.set_index('date', inplace=True)
        elif 'time' in df.columns:
            df.set_index('time', inplace=True)
        elif 'datetime' in df.columns:
            df.set_index('datetime', inplace=True)
    
    # 인덱스가 여전히 DatetimeIndex가 아니면 첫 번째 컬럼이 날짜인지 확인
    if not isinstance(df.index, pd.DatetimeIndex):
        first_col = df.columns[0]
        try:
            df.set_index(first_col, inplace=True)
            df.index = pd.to_datetime(df.index)
        except:
            pass
    
    # 여전히 DatetimeIndex가 아니면 숫자 인덱스 유지
    if not isinstance(df.index, pd.DatetimeIndex):
        print("경고: 데이터프레임에 날짜 인덱스를 설정할 수 없습니다.")
    
    # 필수 컬럼이 없는 경우 빈 데이터프레임 반환
    required_columns = ['open', 'high', 'low', 'close']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"경고: 데이터프레임에 필수 컬럼이 없습니다: {missing_columns}")
        print(f"현재 컬럼: {df.columns.tolist()}")
        return pd.DataFrame(index=df.index)
    
    return df

def add_colormap_to_values(values: np.ndarray, cmap_name: str = 'RdYlGn') -> List[Any]:
    """
    값 배열에 컬러맵 적용
    
    Parameters:
        values (np.ndarray): 컬러맵을 적용할 값 배열
        cmap_name (str): 적용할 컬러맵 이름
        
    Returns:
        List[Any]: 컬러 값 목록
    """
    cmap = plt.get_cmap(cmap_name)
    
    # 값을 0~1 범위로 정규화
    if len(values) > 0:
        vmin, vmax = min(values), max(values)
        if vmin == vmax:
            normalized = np.ones(len(values)) * 0.5
        else:
            normalized = (values - vmin) / (vmax - vmin)
    else:
        normalized = []
    
    # 컬러맵 적용
    return [cmap(x) for x in normalized]

def create_chart_title(ticker: str, chart_type: str, period: str, interval: str,
                     strategy: str = None, additional_info: str = None) -> str:
    """
    차트 제목 생성
    
    Parameters:
        ticker (str): 종목 심볼
        chart_type (str): 차트 유형 ('analysis', 'backtest', 'trading')
        period (str): 기간
        interval (str): 간격
        strategy (str, optional): 전략 이름
        additional_info (str, optional): 추가 정보
        
    Returns:
        str: 생성된 제목
    """
    # 기본 제목
    title = f"{ticker} "
    
    # 차트 유형에 따른 추가 텍스트
    if chart_type == 'analysis':
        title += "기술적 분석 차트"
    elif chart_type == 'backtest':
        title += "백테스팅 결과"
        if strategy:
            title += f" ({strategy} 전략)"
    elif chart_type == 'trading':
        title += "거래 현황"
    
    # 기간 정보 추가
    title += f" ({interval}, {period})"
    
    # 추가 정보
    if additional_info:
        title += f" - {additional_info}"
        
    return title

def calculate_chart_grid_size(num_indicators: int) -> Tuple[int, int]:
    """
    표시할 지표 개수에 따라 그리드 크기 계산
    
    Parameters:
        num_indicators (int): 표시할 지표 개수
        
    Returns:
        Tuple[int, int]: (rows, columns) 그리드 크기
    """
    if num_indicators <= 1:
        return (1, 1)
    elif num_indicators <= 2:
        return (2, 1)
    elif num_indicators <= 4:
        return (2, 2)
    elif num_indicators <= 6:
        return (3, 2)
    else:
        return (4, 2)  # 최대 8개 지표 지원

def adjust_figure_size(num_panels: int) -> Tuple[int, int]:
    """
    패널 수에 따른 그림 크기 조정
    
    Parameters:
        num_panels (int): 패널(서브플롯) 수
        
    Returns:
        Tuple[int, int]: (width, height) 그림 크기
    """
    base_width = 12
    
    # 각 패널 당 평균 높이 계산 (최소 3, 최대 5)
    panel_height = 3 if num_panels <= 2 else max(3, min(5, 16 / num_panels))
    
    # 전체 높이 계산 (16인치를 넘지 않도록)
    height = min(16, num_panels * panel_height)
    
    return (base_width, height)

def apply_common_chart_style(
    fig, 
    axes, 
    ticker: str,
    title: str,
    style_config: Dict[str, Any],
    hide_labels: List[bool] = None
) -> None:
    """
    여러 차트 유형에 공통 스타일과 레이아웃 적용
    
    Parameters:
        fig (Figure): matplotlib 그림 객체
        axes (List[Axes]): 차트 축 객체 리스트
        ticker (str): 종목 심볼
        title (str): 차트 제목
        style_config (Dict[str, Any]): 스타일 설정
        hide_labels (List[bool], optional): 각 축별 x축 레이블 표시 여부
        
    Returns:
        None
    """
    # 차트 배경 설정
    bg_color = style_config['colors'].get('background', '#131722')
    for ax in axes:
        ax.set_facecolor(bg_color)
        
    # 차트 그리드 스타일 통일
    for ax in axes:
        ax.grid(True, alpha=0.15, color=style_config['colors'].get('grid', '#2A2E39'))
        
    # x축 라벨 설정 (마지막 패널만 표시)
    if hide_labels:
        for i, ax in enumerate(axes):
            if i < len(hide_labels) and hide_labels[i]:
                plt.setp(ax.get_xticklabels(), visible=False)
    
    # 제목 설정
    fig.suptitle(
        title,
        fontsize=style_config['fontsize']['title'],
        color=style_config['colors'].get('text', 'white'),
        y=0.98
    )
    
    # 여백 조정 - tight_layout 대신 직접 subplots_adjust 사용
    try:
        # tight_layout 사용하지 않고 직접 여백 설정
        fig.subplots_adjust(top=0.92, bottom=0.1, left=0.1, right=0.95, hspace=0.35)
    except Exception as e:
        print(f"차트 레이아웃 조정 중 경고: {e}") 