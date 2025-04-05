"""
차트 스타일 및 테마 설정 모듈
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
from typing import Dict, Any, Tuple, List

# 색상 팔레트
COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

# 기본 색상 팔레트
DEFAULT_COLORS = {
    # 기본 차트 요소
    'background': '#333333',
    'text': '#FFFFFF',
    'grid': '#555555',
    
    # 가격 및 지표
    'price': '#FFFFFF',
    'volume': '#888888',
    'ma_short': '#FF9500',  # 단기 이동평균선
    'ma_long': '#00BFFF',   # 장기 이동평균선
    'bb_upper': '#FF9500',  # 볼린저 밴드 상단
    'bb_lower': '#00BFFF',  # 볼린저 밴드 하단
    'macd': '#FF9500',      # MACD 선
    'signal': '#00BFFF',    # 시그널 선
    'histogram_positive': '#00FF00',  # 히스토그램 양수
    'histogram_negative': '#FF6347',  # 히스토그램 음수
    
    # 트레이딩 신호
    'buy_signal': '#00FF00',  # 매수 신호
    'sell_signal': '#FF0000', # 매도 신호
    
    # 자산 및 성과 지표
    'asset': '#00FF00',       # 자산 가치
    'drawdown': '#FF6347',    # 드로우다운
    'baseline': '#FFFFFF',    # 기준선 (초기 자본금 등)
    
    # 성과 요약 텍스트
    'profit': '#00FF00',      # 수익 (양수)
    'loss': '#FF6347',        # 손실 (음수)
}

# 라이트 모드 색상 팔레트
LIGHT_COLORS = {
    # 기본 차트 요소
    'background': '#FFFFFF',
    'text': '#000000',
    'grid': '#CCCCCC',
    
    # 가격 및 지표
    'price': '#000000',
    'volume': '#AAAAAA',
    'ma_short': '#FF6600',     # 단기 이동평균선
    'ma_long': '#0066FF',      # 장기 이동평균선
    'bb_upper': '#FF6600',     # 볼린저 밴드 상단
    'bb_lower': '#0066FF',     # 볼린저 밴드 하단
    'macd': '#FF6600',         # MACD 선
    'signal': '#0066FF',       # 시그널 선
    'histogram_positive': '#00AA00',  # 히스토그램 양수
    'histogram_negative': '#DD0000',  # 히스토그램 음수
    
    # 트레이딩 신호
    'buy_signal': '#00AA00',   # 매수 신호
    'sell_signal': '#DD0000',  # 매도 신호
    
    # 자산 및 성과 지표
    'asset': '#00AA00',        # 자산 가치
    'drawdown': '#DD0000',     # 드로우다운
    'baseline': '#000000',     # 기준선 (초기 자본금 등)
    
    # 성과 요약 텍스트
    'profit': '#00AA00',       # 수익 (양수)
    'loss': '#DD0000',         # 손실 (음수)
}

# 차트 스타일 프리셋
STYLE_PRESETS = {
    'default': {
        'figsize': (16, 14),
        'dpi': 300,
        'fontsize': {
            'title': 16,
            'subtitle': 14,
            'label': 12,
            'tick': 10,
            'legend': 10,
            'annotation': 12,
        },
        'colors': DEFAULT_COLORS,
        'alpha': {
            'grid': 0.2,
            'volume': 0.3,
            'baseline': 0.5,
            'fill': 0.5,
        },
        'linewidth': {
            'price': 1.5,
            'ma': 1.0,
            'bb': 0.8,
            'asset': 1.5,
            'drawdown': 1.0,
            'baseline': 1.0,
        },
        'marker': {
            'buy': '^',      # 삼각형 (위)
            'sell': 'v',     # 삼각형 (아래)
            'size': 100,     # 마커 크기
        },
    },
    'light': {
        'figsize': (16, 14),
        'dpi': 300,
        'fontsize': {
            'title': 16,
            'subtitle': 14,
            'label': 12,
            'tick': 10,
            'legend': 10,
            'annotation': 12,
        },
        'colors': LIGHT_COLORS,
        'alpha': {
            'grid': 0.3,
            'volume': 0.5,
            'baseline': 0.7,
            'fill': 0.3,
        },
        'linewidth': {
            'price': 1.5,
            'ma': 1.0,
            'bb': 0.8,
            'asset': 1.5,
            'drawdown': 1.0,
            'baseline': 1.0,
        },
        'marker': {
            'buy': '^',      # 삼각형 (위)
            'sell': 'v',     # 삼각형 (아래)
            'size': 100,     # 마커 크기
        },
    },
}

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
    # Unicode minus 문자 대신 일반 하이픈('-') 사용 설정
    plt.rcParams['axes.unicode_minus'] = False

def apply_style(style: str = 'default') -> Dict[str, Any]:
    """
    지정된 스타일을 적용하고 스타일 설정을 반환합니다.
    
    Parameters:
        style (str): 적용할 스타일 이름 ('default' 또는 'light')
        
    Returns:
        Dict[str, Any]: 스타일 설정 정보
    """
    # 유효한 스타일 프리셋 확인
    if style not in STYLE_PRESETS:
        style = 'default'
    
    # 스타일 설정 가져오기
    style_config = STYLE_PRESETS[style]
    
    # 다크 모드 (기본값) 또는 라이트 모드 설정
    if style == 'light':
        plt.style.use('default')
    else:
        plt.style.use('dark_background')
    
    # 폰트 설정
    plt.rcParams['font.size'] = style_config['fontsize']['tick']
    plt.rcParams['axes.titlesize'] = style_config['fontsize']['subtitle']
    plt.rcParams['axes.labelsize'] = style_config['fontsize']['label']
    plt.rcParams['xtick.labelsize'] = style_config['fontsize']['tick']
    plt.rcParams['ytick.labelsize'] = style_config['fontsize']['tick']
    plt.rcParams['legend.fontsize'] = style_config['fontsize']['legend']
    
    # Unicode minus 문자 대신 일반 하이픈('-') 사용 설정
    plt.rcParams['axes.unicode_minus'] = False
    
    # 배경색 설정 (저장 시에만 적용)
    plt.rcParams['savefig.facecolor'] = style_config['colors']['background']
    
    # 그리드 설정
    plt.rcParams['grid.alpha'] = style_config['alpha']['grid']
    plt.rcParams['grid.color'] = style_config['colors']['grid']
    
    return style_config

def get_color_for_value(value: float, style_config: Dict[str, Any]) -> str:
    """
    값에 따라 적절한 색상 반환 (양수/음수)
    
    Parameters:
        value (float): 색상을 결정할 값
        style_config (Dict[str, Any]): 스타일 설정 정보
        
    Returns:
        str: 색상 코드
    """
    colors = style_config['colors']
    return colors['profit'] if value >= 0 else colors['loss']
