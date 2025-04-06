"""
기본 차트 모듈

기본적인 가격 차트와 공통 차트 요소를 생성하는 함수를 제공합니다.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from mplfinance.original_flavor import candlestick_ohlc
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union, Callable

from src.utils.config import CHART_SAVE_PATH
from src.utils.chart_utils import (
    save_chart, setup_chart_dir, format_date_axis, 
    format_price_axis, generate_filename, detect_chart_type
)
from src.visualization.styles import apply_style, register_mplfinance_style
from src.visualization.viz_helpers import (
    prepare_ohlcv_dataframe, add_colormap_to_values, create_chart_title,
    calculate_chart_grid_size, adjust_figure_size,
    apply_common_chart_style
)

def create_base_chart(
    df: pd.DataFrame,
    ticker: str,
    chart_type: str = 'candlestick',
    chart_dir: Optional[str] = None,
    style: str = 'default',
    interval: str = '1d',
    period: str = '3m',
    figsize: Optional[Tuple[float, float]] = None,
    show_volume: bool = True,
    add_indicators: List[str] = None,
    save: bool = True,
    custom_panels: Optional[int] = None,
    panel_ratios: Optional[List[float]] = None,
    title: Optional[str] = None,
    show_legend: bool = True
) -> Tuple[Figure, List, str]:
    """
    기본 가격 차트 생성
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        ticker (str): 티커 심볼
        chart_type (str): 차트 유형 ('candlestick', 'line', 'ohlc')
        chart_dir (str, optional): 차트 저장 디렉토리
        style (str): 차트 스타일 ('default', 'dark', 'tradingview')
        interval (str): 데이터 간격 ('1m', '5m', '1h', '4h', '1d', '1w')
        period (str): 기간 ('1d', '1w', '1m', '3m', '6m', '1y', 'all')
        figsize (Tuple[float, float], optional): 그림 크기
        show_volume (bool): 거래량 표시 여부
        add_indicators (List[str], optional): 추가할 지표 목록
        save (bool): 차트 저장 여부
        custom_panels (int, optional): 사용자 정의 패널 수
        panel_ratios (List[float], optional): 패널 비율
        title (str, optional): 차트 제목
        show_legend (bool): 범례 표시 여부
        
    Returns:
        Tuple[Figure, List, str]: (fig, axes, 저장된 차트 경로)
    """
    # 차트 디렉토리 설정
    if chart_dir is None:
        chart_dir = setup_chart_dir(CHART_SAVE_PATH)
    
    # 스타일 설정
    style_config = apply_style(style)
    
    # 데이터 전처리
    df = prepare_ohlcv_dataframe(df)
    
    # 지표가 없으면 빈 목록으로 초기화
    if add_indicators is None:
        add_indicators = []
    
    # 패널 수 계산
    total_panels = calculate_chart_grid_size(show_volume, add_indicators, custom_panels)
    
    # 패널 비율 설정
    if panel_ratios is None:
        if total_panels == 1:
            panel_ratios = [1]
        elif total_panels == 2:
            panel_ratios = [3, 1]  # 가격:거래량 = 3:1
        else:
            # 기본 비율: 가격 3, 거래량 1, 나머지 지표 각 1.5
            panel_ratios = [3]  # 가격 패널
            
            if show_volume:
                panel_ratios.append(1)  # 거래량 패널
                
            # 나머지 지표 패널
            panel_ratios.extend([1.5] * (total_panels - (2 if show_volume else 1)))
    
    # 차트 크기 자동 조정
    if figsize is None:
        figsize = adjust_figure_size(total_panels)
    
    # 그리드 설정
    fig = plt.figure(figsize=figsize, dpi=style_config['figure']['dpi'])
    gs = gridspec.GridSpec(total_panels, 1, height_ratios=panel_ratios)
    
    # 차트 제목 설정
    if title is None:
        title = create_chart_title(ticker, chart_type, period, interval)
    plt.suptitle(title, fontsize=style_config['fontsize']['title'])
    
    # 차트 생성
    axes = []
    
    # 메인 차트 (가격)
    ax_price = fig.add_subplot(gs[0])
    axes.append(ax_price)
    
    # 차트 유형에 따라 처리
    if chart_type.lower() == 'candlestick':
        plot_candlestick(ax_price, df, style_config)
    elif chart_type.lower() == 'ohlc':
        plot_ohlc(ax_price, df, style_config)
    else:  # 'line' 또는 기타
        plot_line(ax_price, df, style_config)
    
    # 거래량 차트 추가
    current_panel = 1
    
    if show_volume and 'volume' in df.columns:
        ax_volume = fig.add_subplot(gs[current_panel], sharex=ax_price)
        axes.append(ax_volume)
        plot_volume(ax_volume, df, style_config)
        current_panel += 1
    
    # 다른 패널 추가 (사용자 정의 또는 지표 등)
    for _ in range(current_panel, total_panels):
        ax = fig.add_subplot(gs[_], sharex=ax_price)
        axes.append(ax)
    
    # X축 공유 설정
    for ax in axes[1:]:
        plt.setp(ax.get_xticklabels(), visible=True)
    
    # 축 포맷 설정
    format_date_axis(ax_price)
    format_price_axis(ax_price)
    
    # 레이아웃 조정
    apply_common_chart_style(
        fig=fig, 
        axes=axes, 
        ticker=ticker, 
        title=title if title else create_chart_title(ticker, chart_type, period, interval),
        style_config=style_config
    )
    
    # 차트 저장
    chart_path = ''
    if save:
        filename = generate_filename(ticker, chart_type, interval, period)
        chart_path = os.path.join(chart_dir, filename)
        try:
            # tight layout 대신 여백을 명시적으로 지정
            plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
        except Exception as e:
            print(f"차트 저장 중 경고: {e}")
            # 오류 발생 시 bbox_inches 없이 저장 시도
            plt.savefig(chart_path, dpi=style_config['figure']['dpi'])
    
    return fig, axes, chart_path

def calculate_chart_panels(
    show_volume: bool, 
    add_indicators: List[str], 
    custom_panels: Optional[int] = None
) -> int:
    """
    필요한 차트 패널 수 계산
    
    Parameters:
        show_volume (bool): 거래량 표시 여부
        add_indicators (List[str]): 추가할 지표 목록
        custom_panels (int, optional): 사용자 정의 패널 수
        
    Returns:
        int: 총 패널 수
    """
    if custom_panels is not None:
        return max(custom_panels, 1)  # 최소 1개의 패널 필요
    
    # 기본 패널 (가격)
    panels = 1
    
    # 거래량 패널
    if show_volume:
        panels += 1
    
    # 지표 패널
    if add_indicators:
        # 지표별 필요 패널 수
        indicator_panels = {
            'macd': 1,
            'rsi': 1,
            'stoch': 1,
            'cci': 1,
            'atr': 1,
            'bollinger': 0,  # 볼린저 밴드는 가격 패널에 추가
            'ichimoku': 0,   # 이치모쿠는 가격 패널에 추가
            'support_resistance': 0  # 지지/저항선은 가격 패널에 추가
        }
        
        # 지표별 패널 수 추가
        for indicator in add_indicators:
            indicator_lower = indicator.lower()
            if indicator_lower in indicator_panels:
                panels += indicator_panels[indicator_lower]
            else:
                # 모르는 지표는 기본적으로 새 패널을 추가
                panels += 1
    
    return panels

def plot_candlestick(ax: plt.Axes, df: pd.DataFrame, style_config: Dict[str, Any]) -> None:
    """
    캔들스틱 차트 그리기
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): OHLCV 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
        
    Returns:
        None
    """
    # 캔들스틱을 위한 데이터 준비
    ohlc_data = []
    for date, row in df.iterrows():
        # matplotlib 날짜 형식으로 변환
        date_num = mdates.date2num(date)
        open_price, high_price, low_price, close_price = row['open'], row['high'], row['low'], row['close']
        ohlc_data.append([date_num, open_price, high_price, low_price, close_price])
    
    # 캔들스틱 그리기
    width = style_config['candle']['width']
    up_color = style_config['candle']['colorup']
    down_color = style_config['candle']['colordown']
    alpha = style_config['candle']['alpha']
    
    candlestick_ohlc(
        ax=ax,
        quotes=ohlc_data,
        width=width,
        colorup=up_color,
        colordown=down_color,
        alpha=alpha
    )
    
    # 축 설정
    ax.set_ylabel('가격', fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid']['alpha'])

def plot_ohlc(ax: plt.Axes, df: pd.DataFrame, style_config: Dict[str, Any]) -> None:
    """
    OHLC 차트 그리기
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): OHLCV 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
        
    Returns:
        None
    """
    # OHLC를 위한 데이터 준비
    ohlc_data = []
    for date, row in df.iterrows():
        # matplotlib 날짜 형식으로 변환
        date_num = mdates.date2num(date)
        open_price, high_price, low_price, close_price = row['open'], row['high'], row['low'], row['close']
        ohlc_data.append([date_num, open_price, high_price, low_price, close_price])
    
    # OHLC 그리기 (캔들스틱 함수를 사용하지만 width를 더 작게 설정)
    width = style_config['candle']['width'] * 0.8  # 더 얇게
    up_color = style_config['candle']['colorup']
    down_color = style_config['candle']['colordown']
    
    candlestick_ohlc(
        ax=ax,
        quotes=ohlc_data,
        width=width,
        colorup=up_color,
        colordown=down_color,
        alpha=1.0
    )
    
    # 축 설정
    ax.set_ylabel('가격', fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid']['alpha'])

def plot_line(ax: plt.Axes, df: pd.DataFrame, style_config: Dict[str, Any]) -> None:
    """
    라인 차트 그리기
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): OHLCV 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
        
    Returns:
        None
    """
    # 종가를 이용한 라인 차트
    ax.plot(
        df.index, 
        df['close'], 
        color=style_config['colors']['price'], 
        linewidth=2, 
        label='가격'
    )
    
    # 축 설정
    ax.set_ylabel('가격', fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid']['alpha'])

def plot_volume(ax: plt.Axes, df: pd.DataFrame, style_config: Dict[str, Any]) -> None:
    """
    거래량 차트 그리기
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): OHLCV 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
        
    Returns:
        None
    """
    # 거래량 컬럼이 있는지 확인
    if 'volume' not in df.columns:
        ax.text(0.5, 0.5, '거래량 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 색상 설정 (종가가 시가보다 높으면 매수색, 낮으면 매도색)
    colors = np.where(
        df['close'] >= df['open'],
        style_config['colors']['buy_signal'],
        style_config['colors']['sell_signal']
    )
    
    # 거래량 그리기
    ax.bar(df.index, df['volume'], color=colors, alpha=0.7, width=0.8)
    
    # 축 설정
    ax.set_ylabel('거래량', fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid']['alpha'])
    
    # Y축에 천 단위 구분기호 추가
    ax.yaxis.set_major_formatter(plt.matplotlib.ticker.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))

def add_moving_averages(
    ax: plt.Axes, 
    df: pd.DataFrame, 
    windows: List[int], 
    style_config: Dict[str, Any],
    ma_type: str = 'sma',
    show_legend: bool = True
) -> None:
    """
    이동평균선 추가
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): OHLCV 데이터프레임
        windows (List[int]): 이동평균 기간 리스트
        style_config (Dict[str, Any]): 스타일 설정
        ma_type (str): 이동평균 유형 ('sma', 'ema', 'wma')
        show_legend (bool): 범례 표시 여부
        
    Returns:
        None
    """
    # 이동평균 유형 매핑
    ma_suffix = {
        'sma': 'MA',
        'ema': 'EMA',
        'wma': 'WMA'
    }
    
    suffix = ma_suffix.get(ma_type.lower(), 'MA')
    
    # 기본 MA 색상
    ma_colors = [
        style_config['colors']['ma_short'],  # 단기
        style_config['colors']['ma_medium'], # 중기
        style_config['colors']['ma_long'],   # 장기
        style_config['colors']['ema']        # 추가 (필요시)
    ]
    
    # 이동평균 컬럼이 있는지 확인
    for i, window in enumerate(windows):
        ma_col = f"{ma_type.lower()}{window}"
        
        if ma_col in df.columns:
            color_idx = min(i, len(ma_colors) - 1)
            ax.plot(
                df.index, 
                df[ma_col], 
                color=ma_colors[color_idx], 
                linewidth=1.5, 
                label=f'{window}{suffix}'
            )
        else:
            # 데이터프레임에 이동평균 계산
            if ma_type.lower() == 'sma':
                df[ma_col] = df['close'].rolling(window=window).mean()
            elif ma_type.lower() == 'ema':
                df[ma_col] = df['close'].ewm(span=window, adjust=False).mean()
            elif ma_type.lower() == 'wma':
                weights = np.arange(1, window + 1)
                df[ma_col] = df['close'].rolling(window=window).apply(
                    lambda x: np.sum(weights * x) / weights.sum(), raw=True
                )
            
            color_idx = min(i, len(ma_colors) - 1)
            ax.plot(
                df.index, 
                df[ma_col], 
                color=ma_colors[color_idx], 
                linewidth=1.5, 
                label=f'{window}{suffix}'
            )
    
    # 범례 표시
    if show_legend and windows:
        ax.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])

def add_bollinger_bands(
    ax: plt.Axes, 
    df: pd.DataFrame, 
    style_config: Dict[str, Any],
    window: int = 20, 
    num_std: float = 2.0,
    show_legend: bool = True,
    fill: bool = True
) -> None:
    """
    볼린저 밴드 추가
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): OHLCV 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
        window (int): 이동평균 기간
        num_std (float): 표준편차 배수
        show_legend (bool): 범례 표시 여부
        fill (bool): 밴드 사이를 채울지 여부
        
    Returns:
        None
    """
    # 볼린저 밴드 컬럼 확인
    bb_columns = {
        'middle': f'bb{window}_middle',
        'upper': f'bb{window}_upper',
        'lower': f'bb{window}_lower'
    }
    
    # 밴드 계산 또는 기존 컬럼 사용
    for key, col in bb_columns.items():
        if col not in df.columns:
            if key == 'middle':
                # 중앙선(SMA) 계산
                df[col] = df['close'].rolling(window=window).mean()
            elif key == 'upper':
                # 상단 밴드 계산
                if bb_columns['middle'] not in df.columns:
                    df[bb_columns['middle']] = df['close'].rolling(window=window).mean()
                df[col] = df[bb_columns['middle']] + (df['close'].rolling(window=window).std() * num_std)
            elif key == 'lower':
                # 하단 밴드 계산
                if bb_columns['middle'] not in df.columns:
                    df[bb_columns['middle']] = df['close'].rolling(window=window).mean()
                df[col] = df[bb_columns['middle']] - (df['close'].rolling(window=window).std() * num_std)
    
    # 밴드 그리기
    upper_color = style_config['colors']['bbands_upper']
    lower_color = style_config['colors']['bbands_lower']
    
    # 중앙선
    ax.plot(
        df.index, 
        df[bb_columns['middle']], 
        color=style_config['colors']['ma_medium'], 
        linestyle='-', 
        linewidth=1.2, 
        label=f'BB({window}) 중앙'
    )
    
    # 상단선
    ax.plot(
        df.index, 
        df[bb_columns['upper']], 
        color=upper_color, 
        linestyle='--', 
        linewidth=1.0, 
        label=f'BB({window}) 상단'
    )
    
    # 하단선
    ax.plot(
        df.index, 
        df[bb_columns['lower']], 
        color=lower_color, 
        linestyle='--', 
        linewidth=1.0, 
        label=f'BB({window}) 하단'
    )
    
    # 밴드 사이 채우기
    if fill:
        ax.fill_between(
            df.index, 
            df[bb_columns['upper']], 
            df[bb_columns['lower']], 
            color=upper_color, 
            alpha=0.1
        )
    
    # 범례 표시
    if show_legend:
        ax.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])

def add_support_resistance(
    ax: plt.Axes, 
    df: pd.DataFrame, 
    support_levels: List[float], 
    resistance_levels: List[float],
    style_config: Dict[str, Any]
) -> None:
    """
    지지선과 저항선 추가
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): OHLCV 데이터프레임
        support_levels (List[float]): 지지 레벨 목록
        resistance_levels (List[float]): 저항 레벨 목록
        style_config (Dict[str, Any]): 스타일 설정
        
    Returns:
        None
    """
    # 전체 기간에 걸쳐 수평선 그리기
    xmin, xmax = ax.get_xlim()
    
    # 지지선 그리기
    for level in support_levels:
        ax.axhline(
            y=level, 
            color=style_config['colors']['support'], 
            linestyle='--', 
            linewidth=1.0, 
            alpha=0.7,
            label=f'지지선 {level:,.0f}'
        )
        
        # 레벨 표시
        ax.text(
            xmax, 
            level, 
            f'{level:,.0f}', 
            ha='right', 
            va='center', 
            fontsize=style_config['fontsize']['annotation'],
            color=style_config['colors']['support'],
            alpha=0.9
        )
    
    # 저항선 그리기
    for level in resistance_levels:
        ax.axhline(
            y=level, 
            color=style_config['colors']['resistance'], 
            linestyle='--', 
            linewidth=1.0, 
            alpha=0.7,
            label=f'저항선 {level:,.0f}'
        )
        
        # 레벨 표시
        ax.text(
            xmax, 
            level, 
            f'{level:,.0f}', 
            ha='right', 
            va='center', 
            fontsize=style_config['fontsize']['annotation'],
            color=style_config['colors']['resistance'],
            alpha=0.9
        )

def add_markers(
    ax: plt.Axes, 
    df: pd.DataFrame, 
    buy_signals: Union[pd.Series, List[int]], 
    sell_signals: Union[pd.Series, List[int]],
    style_config: Dict[str, Any]
) -> None:
    """
    매수/매도 신호 마커 추가
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): OHLCV 데이터프레임
        buy_signals (Union[pd.Series, List[int]]): 매수 신호 (True/False 또는 인덱스 목록)
        sell_signals (Union[pd.Series, List[int]]): 매도 신호 (True/False 또는 인덱스 목록)
        style_config (Dict[str, Any]): 스타일 설정
        
    Returns:
        None
    """
    # 시리즈 또는 리스트에 따라 처리
    if isinstance(buy_signals, pd.Series):
        buy_indices = df.index[buy_signals]
        buy_prices = df.loc[buy_signals, 'close']
    else:
        buy_indices = [df.index[i] for i in buy_signals if 0 <= i < len(df)]
        buy_prices = [df.iloc[i]['close'] for i in buy_signals if 0 <= i < len(df)]
    
    if isinstance(sell_signals, pd.Series):
        sell_indices = df.index[sell_signals]
        sell_prices = df.loc[sell_signals, 'close']
    else:
        sell_indices = [df.index[i] for i in sell_signals if 0 <= i < len(df)]
        sell_prices = [df.iloc[i]['close'] for i in sell_signals if 0 <= i < len(df)]
    
    # 매수 신호 마커
    ax.scatter(
        buy_indices, 
        buy_prices, 
        marker='^',  # 삼각형 (위)
        color=style_config['colors']['buy_signal'], 
        s=100, 
        alpha=0.7, 
        label='매수 신호'
    )
    
    # 매도 신호 마커
    ax.scatter(
        sell_indices, 
        sell_prices, 
        marker='v',  # 삼각형 (아래)
        color=style_config['colors']['sell_signal'], 
        s=100, 
        alpha=0.7, 
        label='매도 신호'
    )

def add_annotations(
    ax: plt.Axes, 
    df: pd.DataFrame, 
    annotations: Dict[str, Any],
    style_config: Dict[str, Any]
) -> None:
    """
    차트에 주석 추가
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): OHLCV 데이터프레임
        annotations (Dict[str, Any]): 주석 정보
        style_config (Dict[str, Any]): 스타일 설정
        
    Returns:
        None
    """
    # 주석 정보에 따라 처리
    for annotation in annotations:
        # 필수 정보 확인
        if 'date' not in annotation or 'text' not in annotation:
            continue
        
        date = annotation['date']
        text = annotation['text']
        
        # 날짜를 인덱스로 변환
        if isinstance(date, str):
            try:
                date = pd.to_datetime(date)
            except:
                continue
        
        # 해당 날짜에 가장 가까운 데이터 포인트 찾기
        if date not in df.index:
            closest_date = min(df.index, key=lambda x: abs(x - date))
            date = closest_date
        
        # 위치 정보
        price = annotation.get('price', df.loc[date, 'close'])
        
        # 화살표 스타일
        arrowprops = {
            'arrowstyle': annotation.get('arrow_style', '->'),
            'color': annotation.get('color', style_config['colors']['text']),
            'alpha': annotation.get('alpha', 0.7),
            'linewidth': annotation.get('linewidth', 1.0)
        }
        
        # 글자 속성
        textprops = {
            'size': annotation.get('fontsize', style_config['fontsize']['annotation']),
            'color': annotation.get('color', style_config['colors']['text']),
            'weight': annotation.get('weight', 'normal'),
            'ha': annotation.get('ha', 'center'),
            'va': annotation.get('va', 'bottom')
        }
        
        # 주석 추가
        ax.annotate(
            text, 
            xy=(date, price), 
            xytext=(annotation.get('x_offset', 0), annotation.get('y_offset', 20)), 
            textcoords='offset points',
            arrowprops=arrowprops,
            **textprops
        )

def plot_price_with_indicators(
    df: pd.DataFrame,
    ticker: str,
    chart_type: str = 'candlestick',
    show_volume: bool = True,
    ma_windows: List[int] = [20, 50, 200],
    show_bollinger: bool = False,
    bollinger_window: int = 20,
    bollinger_std: float = 2.0,
    show_support_resistance: bool = False,
    support_levels: Optional[List[float]] = None,
    resistance_levels: Optional[List[float]] = None,
    buy_signals: Optional[Union[pd.Series, List[int]]] = None,
    sell_signals: Optional[Union[pd.Series, List[int]]] = None,
    annotations: Optional[List[Dict[str, Any]]] = None,
    chart_dir: Optional[str] = None,
    style: str = 'default',
    interval: str = '1d',
    period: str = '3m',
    title: Optional[str] = None,
    save: bool = True
) -> Tuple[Figure, List, str]:
    """
    가격과 지표가 포함된 차트 생성
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        ticker (str): 티커 심볼
        chart_type (str): 차트 유형 ('candlestick', 'line', 'ohlc')
        show_volume (bool): 거래량 표시 여부
        ma_windows (List[int]): 이동평균 기간 목록
        show_bollinger (bool): 볼린저 밴드 표시 여부
        bollinger_window (int): 볼린저 밴드 기간
        bollinger_std (float): 볼린저 밴드 표준편차 배수
        show_support_resistance (bool): 지지/저항선 표시 여부
        support_levels (List[float], optional): 지지 레벨 목록
        resistance_levels (List[float], optional): 저항 레벨 목록
        buy_signals (Union[pd.Series, List[int]], optional): 매수 신호
        sell_signals (Union[pd.Series, List[int]], optional): 매도 신호
        annotations (List[Dict[str, Any]], optional): 주석 정보
        chart_dir (str, optional): 차트 저장 디렉토리
        style (str): 차트 스타일
        interval (str): 데이터 간격
        period (str): 기간
        title (str, optional): 차트 제목
        save (bool): 차트 저장 여부
        
    Returns:
        Tuple[Figure, List, str]: (fig, axes, 저장된 차트 경로)
    """
    # 필요한 지표 목록 준비
    add_indicators = []
    if show_bollinger:
        add_indicators.append('bollinger')
    
    # 기본 차트 생성
    fig, axes, chart_path = create_base_chart(
        df=df,
        ticker=ticker,
        chart_type=chart_type,
        chart_dir=chart_dir,
        style=style,
        interval=interval,
        period=period,
        show_volume=show_volume,
        add_indicators=add_indicators,
        save=False,  # 나중에 모든 지표를 추가한 후에 저장
        title=title
    )
    
    # 스타일 설정
    style_config = apply_style(style)
    
    # 가격 축
    ax_price = axes[0]
    
    # 이동평균선 추가
    if ma_windows:
        add_moving_averages(ax_price, df, ma_windows, style_config, 'sma', True)
    
    # 볼린저 밴드 추가
    if show_bollinger:
        add_bollinger_bands(
            ax_price, df, style_config, bollinger_window, bollinger_std, True, True
        )
    
    # 지지/저항선 추가
    if show_support_resistance:
        if support_levels is None:
            support_levels = []
        
        if resistance_levels is None:
            resistance_levels = []
        
        add_support_resistance(ax_price, df, support_levels, resistance_levels, style_config)
    
    # 매수/매도 신호 마커 추가
    if buy_signals is not None or sell_signals is not None:
        if buy_signals is None:
            buy_signals = []
        
        if sell_signals is None:
            sell_signals = []
        
        add_markers(ax_price, df, buy_signals, sell_signals, style_config)
    
    # 주석 추가
    if annotations:
        add_annotations(ax_price, df, annotations, style_config)
    
    # 차트 저장
    if save:
        if chart_dir is None:
            chart_dir = setup_chart_dir(CHART_SAVE_PATH)
        
        filename = generate_filename(ticker, chart_type, interval, period)
        chart_path = os.path.join(chart_dir, filename)
        try:
            # tight layout 대신 여백을 명시적으로 지정
            plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
        except Exception as e:
            print(f"차트 저장 중 경고: {e}")
            # 오류 발생 시 bbox_inches 없이 저장 시도
            plt.savefig(chart_path, dpi=style_config['figure']['dpi'])
    
    return fig, axes, chart_path

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
    
    # tight_layout 대신 직접 여백 조정
    fig.subplots_adjust(top=0.92, bottom=0.1, left=0.1, right=0.95, hspace=0.35)

def get_default_style_config() -> Dict[str, Any]:
    """
    기본 스타일 설정값 반환
    
    Returns:
        Dict[str, Any]: 스타일 설정
    """
    return {
        'colors': {
            'background': '#ffffff',
            'price': '#1f77b4',
            'volume': '#888888',
            'positive': '#26a69a',
            'negative': '#ef5350',
            'grid': '#cccccc',
            'text': '#333333',
            'buy_signal': '#26a69a',
            'sell_signal': '#ef5350',
            'macd': '#2196F3',
            'signal': '#FF9800',
            'histogram_positive': '#26a69a',
            'histogram_negative': '#ef5350',
            'rsi': '#9c27b0',
            'portfolio': '#2196F3',
            'drawdown': '#f44336',
            'overbought': '#ef5350',
            'oversold': '#26a69a'
        },
        'fontsize': {
            'title': 16,
            'axis': 12,
            'label': 12,
            'legend': 10,
            'annotation': 10
        },
        'linewidth': {
            'price': 1.5,
            'signal': 1.0,
            'grid': 0.5,
            'indicator': 1.2
        },
        'grid': {
            'alpha': 0.3,
            'linestyle': '--'
        },
        'figure': {
            'dpi': 150
        }
    }

def plot_price_data(
    ax: plt.Axes,
    df: pd.DataFrame,
    signals: pd.DataFrame = None,
    strategy_name: str = '',
    style_config: Dict[str, Any] = None
) -> None:
    """
    가격 데이터와 거래 신호 그리기
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): 가격 데이터
        signals (pd.DataFrame): 매수/매도 신호
        strategy_name (str): 전략 이름
        style_config (Dict[str, Any]): 스타일 설정
    
    Returns:
        None
    """
    if style_config is None:
        style_config = get_default_style_config()
    
    # 데이터프레임 확인
    if df is None or df.empty:
        ax.text(0.5, 0.5, '가격 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 종가 데이터 확인 (대소문자 처리)
    close_col = None
    for col in ['close', 'Close']:
        if col in df.columns:
            close_col = col
            break
    
    if close_col is None:
        ax.text(0.5, 0.5, '종가 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 가격 데이터 그리기
    ax.plot(
        df.index, 
        df[close_col], 
        color=style_config['colors']['price'], 
        linewidth=style_config['linewidth']['price'], 
        label='가격'
    )
    
    # 거래 신호 그리기 (있는 경우)
    if signals is not None and not signals.empty:
        try:
            # 매수 신호
            buy_signals = signals[signals['type'] == 'buy']
            if not buy_signals.empty:
                buy_prices = []
                buy_dates = []
                
                for idx, row in buy_signals.iterrows():
                    # 날짜와 가격 얻기
                    date = idx if isinstance(idx, pd.Timestamp) else pd.to_datetime(idx)
                    price = row.get('price', None)
                    
                    # 가격이 없으면 해당 날짜의 종가 사용
                    if price is None and date in df.index:
                        price = df.loc[date, close_col]
                    
                    if price is not None:
                        buy_dates.append(date)
                        buy_prices.append(price)
                
                if buy_dates and buy_prices:
                    ax.scatter(
                        buy_dates, 
                        buy_prices, 
                        marker='^', 
                        color=style_config['colors']['buy_signal'], 
                        s=100, 
                        label='매수',
                        zorder=5
                    )
            
            # 매도 신호
            sell_signals = signals[signals['type'] == 'sell']
            if not sell_signals.empty:
                sell_prices = []
                sell_dates = []
                
                for idx, row in sell_signals.iterrows():
                    # 날짜와 가격 얻기
                    date = idx if isinstance(idx, pd.Timestamp) else pd.to_datetime(idx)
                    price = row.get('price', None)
                    
                    # 가격이 없으면 해당 날짜의 종가 사용
                    if price is None and date in df.index:
                        price = df.loc[date, close_col]
                    
                    if price is not None:
                        sell_dates.append(date)
                        sell_prices.append(price)
                
                if sell_dates and sell_prices:
                    ax.scatter(
                        sell_dates, 
                        sell_prices, 
                        marker='v', 
                        color=style_config['colors']['sell_signal'], 
                        s=100, 
                        label='매도',
                        zorder=5
                    )
        except Exception as e:
            print(f"거래 신호 그리기 오류: {e}")
    
    # 축 설정
    ax.set_ylabel('가격', fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid']['alpha'], linestyle=style_config['grid']['linestyle'])
    
    # 범례
    ax.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])
    
    # 제목 설정 (전략 이름이 제공된 경우)
    if strategy_name:
        ax.set_title(f"{strategy_name} 전략", fontsize=style_config['fontsize']['title'])

def format_date_axis(ax: plt.Axes, df_index: pd.DatetimeIndex) -> None:
    """
    날짜 축 포맷 설정
    
    Parameters:
        ax (plt.Axes): 축 객체
        df_index (pd.DatetimeIndex): 데이터프레임 인덱스
    
    Returns:
        None
    """
    # 데이터 길이에 따라 날짜 포맷 설정
    date_range = df_index[-1] - df_index[0]
    days = date_range.days
    
    if days <= 10:  # 10일 이하
        date_format = '%Y-%m-%d'
        interval = 1
    elif days <= 60:  # 2개월 이하
        date_format = '%Y-%m-%d'
        interval = 7
    elif days <= 730:  # 2년 이하
        date_format = '%Y-%m'
        interval = 30
    else:  # 2년 초과
        date_format = '%Y'
        interval = 180
    
    # 날짜 포맷터 설정
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    
    # 눈금 간격 설정
    locator = mdates.DayLocator(interval=interval)
    ax.xaxis.set_major_locator(locator)
    
    # 눈금 레이블 회전
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right') 