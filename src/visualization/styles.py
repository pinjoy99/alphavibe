"""
차트 스타일 모듈

차트 스타일을 정의하고 적용하는 함수들을 제공합니다.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
from typing import Dict, Any, Optional, List

# 스타일 정의
STYLES = {
    'default': {
        'figure': {
            'figsize': (12, 8),
            'dpi': 100,
            'facecolor': 'white',
            'edgecolor': 'white'
        },
        'fontsize': {
            'title': 16,
            'subtitle': 14,
            'label': 12,
            'tick': 10,
            'legend': 10,
            'annotation': 9
        },
        'colors': {
            'price': '#1f77b4',  # 기본 파란색
            'volume': '#7F7F7F',  # 회색
            'ma_short': '#FF9500',  # 주황색
            'ma_medium': '#007AFF',  # 파란색
            'ma_long': '#4CD964',  # 초록색
            'ema': '#FF2D55',  # 빨간색
            'bbands_upper': '#5856D6',  # 보라색
            'bbands_lower': '#5856D6',  # 보라색
            'macd': '#FF9500',  # 주황색
            'macd_signal': '#007AFF',  # 파란색
            'macd_hist_positive': '#4CD964',  # 초록색
            'macd_hist_negative': '#FF3B30',  # 빨간색
            'rsi': '#FF9500',  # 주황색
            'stoch': '#5856D6',  # 보라색
            'stoch_signal': '#FF2D55',  # 빨간색
            'buy_signal': '#4CD964',  # 초록색
            'sell_signal': '#FF3B30',  # 빨간색
            'support': '#4CD964',  # 초록색
            'resistance': '#FF3B30',  # 빨간색
            'grid': '#E5E5EA',  # 연한 회색
            'text': '#000000',  # 검정색
            'profit': '#4CD964',  # 초록색
            'loss': '#FF3B30',  # 빨간색
            'background': '#FFFFFF',  # 흰색
            'candle_up': '#26A69A',  # 초록색
            'candle_down': '#EF5350',  # 빨간색
            'currency': '#5AC8FA',  # 하늘색 (원화 표시용)
            'asset': '#34C759',  # 녹색 (자산 표시용)
            'deposit': '#007AFF',  # 파란색
            'withdraw': '#AF52DE'  # 보라색
        },
        'color_palette': [
            '#1f77b4',  # 파란색
            '#ff7f0e',  # 주황색
            '#2ca02c',  # 초록색
            '#d62728',  # 빨간색
            '#9467bd',  # 보라색
            '#8c564b',  # 갈색
            '#e377c2',  # 분홍색
            '#7f7f7f',  # 회색
            '#bcbd22',  # 연두색
            '#17becf'   # 청록색
        ],
        'grid': {
            'alpha': 0.2,
            'linestyle': '--',
            'linewidth': 0.5
        },
        'candle': {
            'width': 0.8,
            'colorup': '#26A69A',  # 초록색
            'colordown': '#EF5350',  # 빨간색
            'alpha': 1.0
        },
        'linewidth': {
            'price': 1.5,
            'ma': 1.0,
            'bb': 0.8,
            'macd': 1.0,
            'indicator': 1.0
        },
        'alpha': {
            'volume': 0.7,
            'bb_fill': 0.1,
            'support': 0.5,
            'resistance': 0.5
        }
    },
    'dark': {
        'figure': {
            'figsize': (12, 8),
            'dpi': 100,
            'facecolor': '#1C1C1E',
            'edgecolor': '#1C1C1E'
        },
        'fontsize': {
            'title': 16,
            'subtitle': 14,
            'label': 12,
            'tick': 10,
            'legend': 10,
            'annotation': 9
        },
        'colors': {
            'price': '#30D5C8',  # 청록색
            'volume': '#8E8E93',  # 회색
            'ma_short': '#FF9F0A',  # 주황색
            'ma_medium': '#0A84FF',  # 파란색
            'ma_long': '#32D74B',  # 초록색
            'ema': '#FF375F',  # 빨간색
            'bbands_upper': '#5E5CE6',  # 보라색
            'bbands_lower': '#5E5CE6',  # 보라색
            'macd': '#FF9F0A',  # 주황색
            'macd_signal': '#0A84FF',  # 파란색
            'macd_hist_positive': '#32D74B',  # 초록색
            'macd_hist_negative': '#FF453A',  # 빨간색
            'rsi': '#FF9F0A',  # 주황색
            'stoch': '#5E5CE6',  # 보라색
            'stoch_signal': '#FF375F',  # 빨간색
            'buy_signal': '#32D74B',  # 초록색
            'sell_signal': '#FF453A',  # 빨간색
            'support': '#32D74B',  # 초록색
            'resistance': '#FF453A',  # 빨간색
            'grid': '#48484A',  # 연한 회색
            'text': '#FFFFFF',  # 흰색
            'profit': '#32D74B',  # 초록색
            'loss': '#FF453A',  # 빨간색
            'background': '#1C1C1E',  # 어두운 배경
            'candle_up': '#4CAF50',  # 초록색
            'candle_down': '#F44336',  # 빨간색
            'currency': '#64D2FF',  # 하늘색 (원화 표시용)
            'asset': '#30D158',  # 녹색 (자산 표시용)
            'deposit': '#0A84FF',  # 파란색
            'withdraw': '#BF5AF2'  # 보라색
        },
        'color_palette': [
            '#30D5C8',  # 청록색
            '#FF9F0A',  # 주황색
            '#32D74B',  # 초록색
            '#FF453A',  # 빨간색
            '#5E5CE6',  # 보라색
            '#BF5AF2',  # 보라색
            '#FF375F',  # 분홍색
            '#8E8E93',  # 회색
            '#FFD60A',  # 노란색
            '#64D2FF'   # 하늘색
        ],
        'grid': {
            'alpha': 0.3,
            'linestyle': '--',
            'linewidth': 0.5
        },
        'candle': {
            'width': 0.8,
            'colorup': '#4CAF50',  # 초록색
            'colordown': '#F44336',  # 빨간색
            'alpha': 1.0
        },
        'linewidth': {
            'price': 1.5,
            'ma': 1.0,
            'bb': 0.8,
            'macd': 1.0,
            'indicator': 1.0
        },
        'alpha': {
            'volume': 0.7,
            'bb_fill': 0.1,
            'support': 0.5,
            'resistance': 0.5
        }
    },
    'tradingview': {
        'figure': {
            'figsize': (12, 8),
            'dpi': 100,
            'facecolor': '#131722',
            'edgecolor': '#131722'
        },
        'fontsize': {
            'title': 16,
            'subtitle': 14,
            'label': 12,
            'tick': 10,
            'legend': 10,
            'annotation': 9
        },
        'colors': {
            'price': '#B2B5BE',  # 회색
            'volume': '#5D606B',  # 어두운 회색
            'ma_short': '#FF9900',  # 주황색
            'ma_medium': '#2962FF',  # 파란색
            'ma_long': '#00897B',  # 초록색
            'ema': '#F44336',  # 빨간색
            'bbands_upper': '#7B1FA2',  # 보라색
            'bbands_lower': '#7B1FA2',  # 보라색
            'macd': '#FF9900',  # 주황색
            'macd_signal': '#2962FF',  # 파란색
            'macd_hist_positive': '#26A69A',  # 초록색
            'macd_hist_negative': '#EF5350',  # 빨간색
            'rsi': '#FF9900',  # 주황색
            'stoch': '#7B1FA2',  # 보라색
            'stoch_signal': '#F44336',  # 빨간색
            'buy_signal': '#26A69A',  # 초록색
            'sell_signal': '#EF5350',  # 빨간색
            'support': '#26A69A',  # 초록색
            'resistance': '#EF5350',  # 빨간색
            'grid': '#2A2E39',  # 어두운 회색
            'text': '#B2B5BE',  # 회색
            'profit': '#26A69A',  # 초록색
            'loss': '#EF5350',  # 빨간색
            'background': '#131722',  # 어두운 배경
            'candle_up': '#26A69A',  # 초록색
            'candle_down': '#EF5350',  # 빨간색
            'currency': '#64B5F6',  # 하늘색 (원화 표시용)
            'asset': '#26A69A',  # 녹색 (자산 표시용)
            'deposit': '#2962FF',  # 파란색
            'withdraw': '#7B1FA2'  # 보라색
        },
        'color_palette': [
            '#B2B5BE',  # 회색
            '#FF9900',  # 주황색
            '#26A69A',  # 초록색
            '#EF5350',  # 빨간색
            '#7B1FA2',  # 보라색
            '#795548',  # 갈색
            '#E91E63',  # 분홍색
            '#5D606B',  # 어두운 회색
            '#CDDC39',  # 연두색
            '#00E5FF'   # 하늘색
        ],
        'grid': {
            'alpha': 0.2,
            'linestyle': '--',
            'linewidth': 0.5
        },
        'candle': {
            'width': 0.8,
            'colorup': '#26A69A',  # 초록색
            'colordown': '#EF5350',  # 빨간색
            'alpha': 1.0
        },
        'linewidth': {
            'price': 1.5,
            'ma': 1.0,
            'bb': 0.8,
            'macd': 1.0,
            'indicator': 1.0
        },
        'alpha': {
            'volume': 0.7,
            'bb_fill': 0.1,
            'support': 0.5,
            'resistance': 0.5
        }
    }
}

def apply_style(style_name: str = 'default') -> Dict[str, Any]:
    """
    차트 스타일을 설정하고 스타일 설정을 반환합니다.
    
    Parameters:
        style_name (str): 스타일 이름 ('default', 'dark', 'tradingview')
    
    Returns:
        Dict[str, Any]: 스타일 설정
    """
    if style_name not in STYLES:
        style_name = 'default'
        print(f"경고: '{style_name}' 스타일이 존재하지 않습니다. 기본 스타일을 사용합니다.")
    
    style_config = STYLES[style_name]
    
    # 전역 스타일 설정
    plt.rcParams['figure.figsize'] = style_config['figure']['figsize']
    plt.rcParams['figure.dpi'] = style_config['figure']['dpi']
    plt.rcParams['figure.facecolor'] = style_config['figure']['facecolor']
    plt.rcParams['figure.edgecolor'] = style_config['figure']['edgecolor']
    
    # 폰트 설정
    plt.rcParams['font.size'] = style_config['fontsize']['tick']
    plt.rcParams['axes.titlesize'] = style_config['fontsize']['title']
    plt.rcParams['axes.labelsize'] = style_config['fontsize']['label']
    plt.rcParams['xtick.labelsize'] = style_config['fontsize']['tick']
    plt.rcParams['ytick.labelsize'] = style_config['fontsize']['tick']
    plt.rcParams['legend.fontsize'] = style_config['fontsize']['legend']
    
    # 색상 설정
    plt.rcParams['axes.facecolor'] = style_config['colors']['background']
    plt.rcParams['axes.edgecolor'] = style_config['colors']['text']
    plt.rcParams['axes.labelcolor'] = style_config['colors']['text']
    plt.rcParams['xtick.color'] = style_config['colors']['text']
    plt.rcParams['ytick.color'] = style_config['colors']['text']
    plt.rcParams['text.color'] = style_config['colors']['text']
    
    # 그리드 설정
    plt.rcParams['grid.alpha'] = style_config['grid']['alpha']
    plt.rcParams['grid.linestyle'] = style_config['grid']['linestyle']
    plt.rcParams['grid.linewidth'] = style_config['grid']['linewidth']
    plt.rcParams['grid.color'] = style_config['colors']['grid']
    
    return style_config

def create_custom_style(
    name: str,
    base_style: str = 'default',
    colors: Optional[Dict[str, str]] = None,
    fontsizes: Optional[Dict[str, int]] = None,
    figure_params: Optional[Dict[str, Any]] = None,
    grid_params: Optional[Dict[str, Any]] = None,
    candle_params: Optional[Dict[str, Any]] = None,
    color_palette: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    커스텀 차트 스타일 생성
    
    Parameters:
        name (str): 새 스타일 이름
        base_style (str): 기반이 될 스타일 이름
        colors (Dict[str, str], optional): 색상 설정
        fontsizes (Dict[str, int], optional): 폰트 크기 설정
        figure_params (Dict[str, Any], optional): 그림 매개변수
        grid_params (Dict[str, Any], optional): 그리드 매개변수
        candle_params (Dict[str, Any], optional): 캔들 매개변수
        color_palette (List[str], optional): 색상 팔레트
        
    Returns:
        Dict[str, Any]: 새 스타일 설정
    """
    # 기본 스타일 복사
    if base_style not in STYLES:
        base_style = 'default'
        print(f"경고: '{base_style}' 스타일이 존재하지 않습니다. 기본 스타일을 사용합니다.")
    
    new_style = STYLES[base_style].copy()
    
    # 스타일 항목 업데이트
    if colors:
        new_style['colors'].update(colors)
    
    if fontsizes:
        new_style['fontsize'].update(fontsizes)
    
    if figure_params:
        new_style['figure'].update(figure_params)
    
    if grid_params:
        new_style['grid'].update(grid_params)
    
    if candle_params:
        new_style['candle'].update(candle_params)
    
    if color_palette:
        new_style['color_palette'] = color_palette
    
    # 새 스타일 등록
    STYLES[name] = new_style
    
    return new_style

def register_mplfinance_style(style_name: str = 'default') -> Dict[str, Any]:
    """
    mplfinance에서 사용할 수 있는 스타일을 등록하고 반환합니다.
    
    Parameters:
        style_name (str): 스타일 이름
        
    Returns:
        Dict[str, Any]: mplfinance 스타일 설정
    """
    if style_name not in STYLES:
        style_name = 'default'
        print(f"경고: '{style_name}' 스타일이 존재하지 않습니다. 기본 스타일을 사용합니다.")
    
    style_config = STYLES[style_name]
    
    # mplfinance 스타일 설정
    mpf_style = {
        'base_mpf_style': 'yahoo',  # 기본 스타일
        'marketcolors': {
            'candle': {
                'up': style_config['candle']['colorup'],
                'down': style_config['candle']['colordown']
            },
            'edge': {
                'up': style_config['candle']['colorup'],
                'down': style_config['candle']['colordown']
            },
            'wick': {
                'up': style_config['candle']['colorup'],
                'down': style_config['candle']['colordown']
            },
            'ohlc': {
                'up': style_config['candle']['colorup'],
                'down': style_config['candle']['colordown']
            },
            'volume': {
                'up': style_config['colors']['buy_signal'],
                'down': style_config['colors']['sell_signal']
            },
            'vcedge': {
                'up': style_config['colors']['buy_signal'],
                'down': style_config['colors']['sell_signal']
            },
            'alpha': style_config['candle']['alpha']
        },
        'mavcolors': [
            style_config['colors']['ma_short'],
            style_config['colors']['ma_medium'],
            style_config['colors']['ma_long'],
            style_config['colors']['ema']
        ],
        'facecolor': style_config['colors']['background'],
        'edgecolor': style_config['colors']['text'],
        'figcolor': style_config['colors']['background'],
        'gridcolor': style_config['colors']['grid'],
        'gridstyle': style_config['grid']['linestyle'],
        'gridaxis': 'both',
        'y_on_right': False,
        'rc': {
            'figure.figsize': style_config['figure']['figsize'],
            'figure.facecolor': style_config['colors']['background'],
            'axes.facecolor': style_config['colors']['background'],
            'axes.edgecolor': style_config['colors']['text'],
            'axes.labelcolor': style_config['colors']['text'],
            'axes.titlesize': style_config['fontsize']['title'],
            'axes.labelsize': style_config['fontsize']['label'],
            'xtick.color': style_config['colors']['text'],
            'ytick.color': style_config['colors']['text'],
            'text.color': style_config['colors']['text'],
            'legend.fontsize': style_config['fontsize']['legend']
        }
    }
    
    return mpf_style

def get_available_styles() -> List[str]:
    """
    사용 가능한 모든 스타일 이름 목록을 반환합니다.
    
    Returns:
        List[str]: 스타일 이름 목록
    """
    return list(STYLES.keys())
