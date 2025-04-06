"""
시장 분석 차트 모듈

시장 분석에 사용되는 차트를 생성하는 함수를 제공합니다.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from typing import Dict, List, Tuple, Optional, Any, Union

from src.indicators import calculate_indicators
from src.indicators.support_resistance import find_support_resistance_levels
from src.utils.config import CHART_SAVE_PATH
from src.utils.chart_utils import (
    format_date_axis, format_price_axis, save_chart, generate_filename, 
    setup_chart_dir, detect_chart_type
)
from src.visualization.styles import apply_style
from src.visualization.viz_helpers import (
    prepare_ohlcv_dataframe, create_chart_title, adjust_figure_size
)
from src.visualization.base_charts import apply_common_chart_style
from src.visualization.indicator_charts import plot_macd, plot_rsi, plot_volume

def plot_market_analysis(
    df: pd.DataFrame, 
    ticker: str, 
    chart_dir: str = CHART_SAVE_PATH, 
    style: str = 'tradingview',
    interval: str = 'day',
    period: str = '3m',
    indicator_config: Optional[Dict[str, bool]] = None
) -> str:
    """
    시장 분석 차트 생성
    
    Parameters:
        df (pd.DataFrame): 주가 데이터 (OHLCV 포함)
        ticker (str): 종목 심볼
        chart_dir (str): 차트 저장 디렉토리
        style (str): 차트 스타일 ('default', 'dark', 'light', 'pro')
        interval (str): 데이터 간격 ('day', 'hour', 'minute')
        period (str): 데이터 기간 ('1d', '5d', '1m', '3m', '6m', '1y')
        indicator_config (Optional[Dict[str, bool]]): 표시할 지표 설정
        
    Returns:
        str: 저장된 차트 파일 경로
    """
    # 데이터프레임 준비
    df = prepare_ohlcv_dataframe(df)
    
    # 데이터프레임 컬럼 디버깅
    print(f"차트 생성 전 데이터프레임 컬럼: {df.columns.tolist()}")
    
    # 기본 지표 설정 (기본값은 모두 표시)
    if indicator_config is None:
        indicator_config = {
            'ma': True,          # 이동평균선
            'volume': True,      # 거래량
            'bb': True,          # 볼린저 밴드
            'macd': True,        # MACD
            'rsi': True,         # RSI
            'stochastic': False, # 스토캐스틱
            'support_resistance': True  # 지지/저항선
        }
    
    # 차트 스타일 가져오기
    style_config = apply_style(style)
    
    # 지표 계산 (indicators 모듈 사용)
    # df에 지표 컬럼이 없으면 계산
    if not any(col.startswith(('sma', 'ema', 'bb', 'macd', 'rsi')) for col in df.columns):
        print("지표 데이터가 없어 계산합니다...")
        df = calculate_indicators(df)
    
    # 지표 데이터 확인
    indicator_cols = [col for col in df.columns if col.startswith(('sma', 'ema', 'bb', 'macd', 'rsi'))]
    print(f"지표 컬럼: {indicator_cols}")
    
    # 지지/저항선 찾기
    if indicator_config.get('support_resistance', True):
        support_levels, resistance_levels = find_support_resistance_levels(df)
    else:
        support_levels, resistance_levels = [], []
    
    # 활성화된 패널 수 확인
    active_panels = 1  # 가격 차트는 항상 포함
    if indicator_config.get('volume', True):
        active_panels += 1
    if indicator_config.get('macd', True):
        active_panels += 1
    if indicator_config.get('rsi', True):
        active_panels += 1
        
    # 그림 크기 조정 및 생성
    fig = plt.figure(figsize=adjust_figure_size(active_panels))
    
    # 그리드 레이아웃 설정
    height_ratios = [2]  # 가격 차트는 2배 높이
    if indicator_config.get('volume', True):
        height_ratios.append(0.5)
    if indicator_config.get('macd', True):
        height_ratios.append(0.8)
    if indicator_config.get('rsi', True):
        height_ratios.append(0.8)
    
    gridspec = plt.GridSpec(len(height_ratios), 1, height_ratios=height_ratios, hspace=0.1)
    
    # 패널 인덱스 및 축 목록 초기화
    panel_idx = 0
    axes = []
    
    # 패널 1: 가격 차트 (항상 포함)
    ax1 = plt.subplot(gridspec[panel_idx])
    axes.append(ax1)
    panel_idx += 1
    
    # 차트 타입 감지 및 시각화
    chart_type = detect_chart_type(df)
    
    # 캔들스틱 차트
    if chart_type == 'candlestick':
        up_color = style_config['colors'].get('up', '#ff9696')
        down_color = style_config['colors'].get('down', '#9ad9ff')
        
        # 상승/하락 캔들 구분
        up = df[df['close'] >= df['open']]
        down = df[df['close'] < df['open']]
        
        # 캔들스틱 그리기
        ax1.bar(up.index, up['high'] - up['low'], width=0.5, bottom=up['low'], color=up_color, alpha=0.8)
        ax1.bar(up.index, up['close'] - up['open'], width=0.8, bottom=up['open'], color=up_color, alpha=1)
        ax1.bar(down.index, down['high'] - down['low'], width=0.5, bottom=down['low'], color=down_color, alpha=0.8)
        ax1.bar(down.index, down['open'] - down['close'], width=0.8, bottom=down['close'], color=down_color, alpha=1)
    else:
        # 라인 차트
        ax1.plot(df.index, df['close'], color=style_config['colors']['price'], linewidth=style_config['linewidth']['price'])

    # 이동평균선 추가
    if indicator_config.get('ma', True):
        ma_cols = [col for col in df.columns if col.startswith(('sma', 'ema'))]
        for col in ma_cols:
            try:
                if col.startswith('sma'):
                    parts = col.split('_')
                    if len(parts) > 1:
                        window = int(parts[1])
                    else:
                        window = int(col.replace('sma', ''))
                    
                    ax1.plot(df.index, df[col], 
                            color=style_config['colors']['ma_short'], 
                            linewidth=style_config['linewidth']['ma'], 
                            label=f'SMA {window}')
                elif col.startswith('ema'):
                    parts = col.split('_')
                    if len(parts) > 1:
                        window = int(parts[1])
                    else:
                        window = int(col.replace('ema', ''))
                        
                    ax1.plot(df.index, df[col], 
                            color=style_config['colors']['ma_long'], 
                            linewidth=style_config['linewidth']['ma'], 
                            label=f'EMA {window}')
            except ValueError:
                # 숫자를 파싱할 수 없는 경우 일반 레이블 사용
                ax1.plot(df.index, df[col], 
                        color=style_config['colors']['ma_medium'], 
                        linewidth=style_config['linewidth']['ma'], 
                        label=col.upper())
    
    # 볼린저 밴드 추가
    if indicator_config.get('bb', True):
        # 볼린저 밴드 관련 컬럼 찾기
        bb_cols = [col for col in df.columns if col.startswith('bb')]
        
        if bb_cols:
            # 다양한 형식 처리 ('bb_upper', 'bbupper', 'BB_UPPER' 등)
            bb_upper_col = None
            bb_lower_col = None
            bb_middle_col = None
            
            # 중간, 상단, 하단 밴드 컬럼 찾기
            for col in bb_cols:
                if 'upper' in col.lower():
                    bb_upper_col = col
                elif 'lower' in col.lower():
                    bb_lower_col = col
                elif 'middle' in col.lower() or 'mid' in col.lower():
                    bb_middle_col = col
            
            # 중간값이 없으면 첫번째 컬럼을 사용
            if not bb_middle_col and len(bb_cols) > 0:
                for col in bb_cols:
                    if 'upper' not in col.lower() and 'lower' not in col.lower():
                        bb_middle_col = col
                        break
            
            # 상단 밴드
            if bb_upper_col and bb_lower_col:
                # 상단 밴드
                ax1.plot(df.index, df[bb_upper_col], 
                        color=style_config['colors']['bbands_upper'], 
                        linewidth=style_config['linewidth']['bb'], 
                        linestyle='--', 
                        label='BB Upper')
                
                # 하단 밴드
                ax1.plot(df.index, df[bb_lower_col], 
                        color=style_config['colors']['bbands_lower'], 
                        linewidth=style_config['linewidth']['bb'], 
                        linestyle='--', 
                        label='BB Lower')
                
                # 중간 밴드 (있으면)
                if bb_middle_col:
                    ax1.plot(df.index, df[bb_middle_col], 
                            color=style_config['colors']['ma_medium'], 
                            linewidth=style_config['linewidth']['bb'], 
                            linestyle='-', 
                            label='BB Middle')
                
                # 밴드 사이 영역 채우기
                ax1.fill_between(
                    df.index, 
                    df[bb_upper_col], 
                    df[bb_lower_col], 
                    color=style_config['colors'].get('price', 'blue'), 
                    alpha=style_config['alpha'].get('bb_fill', 0.1)
                )
    
    # 지지/저항선 추가
    if indicator_config.get('support_resistance', True):
        for level in support_levels:
            ax1.axhline(
                y=level, 
                color=style_config['colors'].get('support', 'green'), 
                linestyle='--', 
                alpha=style_config['alpha'].get('support', 0.3), 
                linewidth=1
            )
        
        for level in resistance_levels:
            ax1.axhline(
                y=level, 
                color=style_config['colors'].get('resistance', 'red'), 
                linestyle='--', 
                alpha=style_config['alpha'].get('resistance', 0.3), 
                linewidth=1
            )
    
    # 가격 축 설정
    format_price_axis(ax1)
    ax1.set_ylabel('가격 (KRW)', fontsize=style_config['fontsize']['label'])
    ax1.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])
    
    # 거래량 패널 추가
    if indicator_config.get('volume', True):
        ax2 = plt.subplot(gridspec[panel_idx], sharex=ax1)
        axes.append(ax2)
        panel_idx += 1
        
        # indicator_charts의 plot_volume 사용
        plot_volume(ax2, df, style_config)
    
    # MACD 패널 추가
    if indicator_config.get('macd', True):
        ax_macd = plt.subplot(gridspec[panel_idx], sharex=ax1)
        axes.append(ax_macd)
        panel_idx += 1
        
        # indicator_charts의 plot_macd 사용
        plot_macd(ax_macd, df, style_config)
    
    # RSI 패널 추가
    if indicator_config.get('rsi', True):
        ax_rsi = plt.subplot(gridspec[panel_idx], sharex=ax1)
        axes.append(ax_rsi)
        panel_idx += 1
        
        # indicator_charts의 plot_rsi 사용
        plot_rsi(ax_rsi, df, style_config)
    
    # 각 패널의 x축 레이블 표시 여부 설정 (마지막 패널만 표시)
    hide_labels = [True] * (len(axes) - 1) + [False]
    
    # 차트 제목 생성
    title = create_chart_title(ticker, 'analysis', period, interval)
    
    # 공통 스타일 적용
    apply_common_chart_style(fig, axes, ticker, title, style_config, hide_labels)
    
    # 차트 저장
    chart_dir = setup_chart_dir(chart_dir)
    filename = generate_filename(ticker, 'analysis', interval, period)
    chart_path = os.path.join(chart_dir, filename)
    plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
    
    return chart_path

def plot_technical_indicators(
    df: pd.DataFrame,
    ticker: str,
    indicators: List[str],
    chart_dir: str = CHART_SAVE_PATH,
    style: str = 'default',
    interval: str = 'day',
    period: str = '1m'
) -> str:
    """
    기술적 지표만 분리하여 표시하는 차트 생성
    
    Parameters:
        df (pd.DataFrame): 주가 데이터 (OHLCV 포함)
        ticker (str): 종목 심볼
        indicators (List[str]): 표시할 지표 목록
        chart_dir (str): 차트 저장 디렉토리
        style (str): 차트 스타일
        interval (str): 데이터 간격
        period (str): 데이터 기간
        
    Returns:
        str: 저장된 차트 파일 경로
    """
    # 데이터프레임 준비
    df = prepare_ohlcv_dataframe(df)
    
    # 지표 계산
    df_with_indicators = calculate_indicators(df)
    
    # 차트 스타일 가져오기
    style_config = apply_style(style)
    
    # 유효한 지표만 필터링
    valid_indicators = [ind for ind in indicators if any(ind in col for col in df_with_indicators.columns)]
    
    if not valid_indicators:
        print(f"경고: 선택한 지표 중 유효한 지표가 없습니다.")
        return ""
    
    # 그래프 레이아웃 설정 (가격 + 각 지표별 패널)
    n_panels = len(valid_indicators) + 1  # 가격 패널 + 지표 패널
    fig, axes = plt.subplots(n_panels, 1, figsize=adjust_figure_size(n_panels), sharex=True)
    
    if n_panels == 1:
        axes = [axes]
    
    # 메인 타이틀 설정
    plt.suptitle(
        create_chart_title(ticker, 'analysis', period, interval, additional_info="기술적 지표"),
        fontsize=style_config['fontsize']['title'],
        y=0.98
    )
    
    # 패널 1: 가격 차트
    ax1 = axes[0]
    
    # 종가 그리기
    ax1.plot(df.index, df['Close'], color=style_config['colors']['price'], 
             linewidth=style_config['linewidth']['price'], label='가격')
    
    # 축 포맷 설정
    format_price_axis(ax1)
    format_date_axis(ax1, hide_labels=True)
    
    ax1.set_ylabel('가격 (KRW)', fontsize=style_config['fontsize']['label'])
    ax1.set_title(f'{ticker} 차트 ({interval}, {period})', fontsize=style_config['fontsize']['subtitle'])
    
    # 지표 패널
    for i, indicator in enumerate(valid_indicators, 1):
        ax = axes[i]
        
        # 해당 지표와 관련된 컬럼들 추출
        indicator_cols = [col for col in df_with_indicators.columns if indicator in col]
        
        # 각 컬럼 그리기
        for col in indicator_cols:
            color_key = col.lower().replace('_', '')
            color = style_config['colors'].get(color_key, style_config['colors'].get('price', 'blue'))
            ax.plot(df_with_indicators.index, df_with_indicators[col], 
                   color=color, label=col)
        
        # 특수 케이스 처리 (RSI, 스토캐스틱 등 - 범위가 0-100인 지표)
        if any(ind in indicator.upper() for ind in ['RSI', 'STOCH']):
            ax.axhline(y=70, color='red', linestyle='--', alpha=0.3)
            ax.axhline(y=30, color='green', linestyle='--', alpha=0.3)
            ax.set_ylim(0, 100)
        
        # MACD 히스토그램
        if 'MACD' in indicator.upper() and 'MACD_HIST' in df_with_indicators.columns:
            hist_colors = np.where(
                df_with_indicators['MACD_HIST'] >= 0, 
                style_config['colors'].get('macd_hist_positive', 'green'), 
                style_config['colors'].get('macd_hist_negative', 'red')
            )
            ax.bar(df_with_indicators.index, df_with_indicators['MACD_HIST'], 
                  color=hist_colors, alpha=0.7, width=0.8)
            ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        
        # 축 포맷 설정
        format_date_axis(ax, hide_labels=(i < len(valid_indicators)))
        
        ax.set_ylabel(indicator, fontsize=style_config['fontsize']['label'])
        ax.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])
    
    # 차트 파일 이름 생성 및 저장
    file_name = generate_filename(ticker=ticker, interval=interval, period=period, 
                                suffix=f"indicators_{len(valid_indicators)}")
    return save_chart(fig, file_name, chart_dir, style_config['figure']['dpi'])

def plot_support_resistance(
    df: pd.DataFrame,
    ticker: str,
    chart_dir: str = CHART_SAVE_PATH,
    style: str = 'default',
    interval: str = 'day',
    period: str = '1m'
) -> str:
    """
    지지선/저항선 차트 생성
    
    Parameters:
        df (pd.DataFrame): 주가 데이터 (OHLCV 포함)
        ticker (str): 종목 심볼
        chart_dir (str): 차트 저장 디렉토리
        style (str): 차트 스타일
        interval (str): 데이터 간격
        period (str): 데이터 기간
        
    Returns:
        str: 저장된 차트 파일 경로
    """
    # 데이터프레임 준비
    df = prepare_ohlcv_dataframe(df)
    
    # 차트 스타일 가져오기
    style_config = apply_style(style)
    
    # 지지/저항선 찾기
    support_levels, resistance_levels = find_support_resistance_levels(df)
    
    # 그래프 설정
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 종가 그리기
    ax.plot(df.index, df['Close'], color=style_config['colors']['price'], 
           linewidth=style_config['linewidth']['price'], label='가격')
    
    # 지지선 그리기
    for level in support_levels:
        ax.axhline(
            y=level, 
            color=style_config['colors'].get('support', 'green'), 
            linestyle='--', 
            alpha=0.6, 
            linewidth=1.5,
            label=f'지지선 ({level:,.0f})'
        )
    
    # 저항선 그리기
    for level in resistance_levels:
        ax.axhline(
            y=level, 
            color=style_config['colors'].get('resistance', 'red'), 
            linestyle='--', 
            alpha=0.6, 
            linewidth=1.5,
            label=f'저항선 ({level:,.0f})'
        )
    
    # 축 포맷 설정
    format_price_axis(ax)
    format_date_axis(ax)
    
    # 차트 정보 설정
    ax.set_title(f'{ticker} 지지/저항선 분석 ({interval}, {period})', 
                fontsize=style_config['fontsize']['title'])
    ax.set_ylabel('가격 (KRW)', fontsize=style_config['fontsize']['label'])
    ax.legend(loc='best', fontsize=style_config['fontsize']['legend'])
    
    # 차트 파일 이름 생성 및 저장
    file_name = generate_filename(ticker=ticker, interval=interval, period=period, 
                                suffix="support_resistance")
    return save_chart(fig, file_name, chart_dir, style_config['figure']['dpi']) 