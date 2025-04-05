"""
차트 생성 관련 함수 모듈
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Union

from src.visualization.styles import apply_style, get_color_for_value
from src.visualization.utils import (
    format_date_axis, 
    format_price_axis, 
    save_chart, 
    generate_filename
)

def plot_price_chart(
    df: pd.DataFrame, 
    ticker: str,
    ma_periods: List[int] = [20],
    volume: bool = True,
    chart_dir: str = 'charts',
    style: str = 'default'
) -> str:
    """
    기본 가격 차트 생성
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        ticker (str): 종목 심볼
        ma_periods (List[int]): 이동평균선 기간 목록
        volume (bool): 거래량 표시 여부
        chart_dir (str): 차트 저장 디렉토리
        style (str): 차트 스타일
        
    Returns:
        str: 저장된 차트 파일 경로
    """
    # 스타일 적용
    style_config = apply_style(style)
    colors = style_config['colors']
    
    # 서브플롯 구성 (거래량 표시 여부에 따라)
    if volume and 'volume' in df.columns:
        fig, (ax1, ax2) = plt.subplots(
            2, 1, 
            figsize=style_config['figsize'],
            gridspec_kw={'height_ratios': [3, 1], 'hspace': 0}
        )
    else:
        fig, ax1 = plt.subplots(figsize=style_config['figsize'])
    
    # 메인 가격 차트
    ax1.plot(df.index, df['close'], color=colors['price'], 
             linewidth=style_config['linewidth']['price'], label='가격')
    
    # 이동평균선 그리기
    ma_colors = [colors['ma_short'], colors['ma_long'], colors['grid']]
    for i, period in enumerate(ma_periods):
        if i < len(ma_colors):  # 사용 가능한 색상이 있는 경우
            ma = df['close'].rolling(window=period).mean()
            ax1.plot(df.index, ma, color=ma_colors[i], 
                     linewidth=style_config['linewidth']['ma'], 
                     label=f'{period}일 이동평균')
    
    # 차트 타이틀 및 레이블
    ax1.set_title(f'{ticker} 가격 차트', fontsize=style_config['fontsize']['title'])
    ax1.set_ylabel('가격 (KRW)', fontsize=style_config['fontsize']['label'])
    ax1.grid(True, alpha=style_config['alpha']['grid'])
    ax1.legend(loc='best', fontsize=style_config['fontsize']['legend'])
    
    # X축 날짜 포맷 설정
    format_date_axis(ax1)
    
    # 거래량 차트 (옵션)
    if volume and 'volume' in df.columns:
        ax2.bar(df.index, df['volume'], color=colors['volume'], 
                alpha=style_config['alpha']['volume'], width=0.8)
        ax2.set_ylabel('거래량', fontsize=style_config['fontsize']['label'])
        ax2.grid(True, alpha=style_config['alpha']['grid'])
        format_date_axis(ax2)
        
        # X축 레이블은 하단 차트에만 표시
        ax1.set_xticklabels([])
    
    # 차트 파일 이름 생성 및 저장
    file_name = generate_filename('chart', ticker)
    return save_chart(fig, file_name, chart_dir, style_config['dpi'])

def plot_trade_signals(
    ax: plt.Axes,
    df: pd.DataFrame,
    buy_points: List[datetime],
    sell_points: List[datetime],
    style_config: Dict[str, Any],
    max_signals: int = 20
) -> None:
    """
    매수/매도 신호를 차트에 표시
    
    Parameters:
        ax (plt.Axes): matplotlib 축 객체
        df (pd.DataFrame): OHLCV 데이터프레임
        buy_points (List[datetime]): 매수 시점 목록
        sell_points (List[datetime]): 매도 시점 목록
        style_config (Dict[str, Any]): 스타일 설정
        max_signals (int): 최대 표시할 신호 개수
    """
    colors = style_config['colors']
    markers = style_config['marker']
    
    # 신호가 많을 경우 샘플링 (가시성 확보)
    sample_factor = max(1, len(buy_points) // max_signals)
    sampled_buy_points = buy_points[::sample_factor]
    
    sample_factor = max(1, len(sell_points) // max_signals)
    sampled_sell_points = sell_points[::sample_factor]
    
    # 매수 신호 표시
    for i, bp in enumerate(sampled_buy_points):
        if bp in df.index:
            ax.scatter(
                bp, df.loc[bp, 'close'], 
                color=colors['buy_signal'], 
                s=markers['size'], 
                marker=markers['buy'], 
                label='매수' if i == 0 else ""
            )
    
    # 매도 신호 표시
    for i, sp in enumerate(sampled_sell_points):
        if sp in df.index:
            ax.scatter(
                sp, df.loc[sp, 'close'], 
                color=colors['sell_signal'], 
                s=markers['size'], 
                marker=markers['sell'], 
                label='매도' if i == 0 else ""
            )

def plot_strategy_indicators(
    ax: plt.Axes,
    df: pd.DataFrame,
    strategy: str,
    style_config: Dict[str, Any]
) -> None:
    """
    전략별 지표를 차트에 표시
    
    Parameters:
        ax (plt.Axes): matplotlib 축 객체
        df (pd.DataFrame): 지표가 포함된 데이터프레임
        strategy (str): 전략 이름
        style_config (Dict[str, Any]): 스타일 설정
    """
    colors = style_config['colors']
    linewidths = style_config['linewidth']
    
    # SMA 전략 지표
    if strategy == 'SMA' and 'short_ma' in df.columns and 'long_ma' in df.columns:
        ax.plot(df.index, df['short_ma'], color=colors['ma_short'], 
                linewidth=linewidths['ma'], label='단기 이동평균선')
        ax.plot(df.index, df['long_ma'], color=colors['ma_long'], 
                linewidth=linewidths['ma'], label='장기 이동평균선')
    
    # 볼린저 밴드 전략 지표
    elif strategy == 'BB' and 'upper_band' in df.columns and 'lower_band' in df.columns:
        ax.plot(df.index, df['upper_band'], color=colors['bb_upper'], 
                linewidth=linewidths['bb'], linestyle='--', label='상단 밴드')
        if 'ma' in df.columns:
            ax.plot(df.index, df['ma'], color=colors['ma_short'], 
                    linewidth=linewidths['ma'], label='중앙선')
        ax.plot(df.index, df['lower_band'], color=colors['bb_lower'], 
                linewidth=linewidths['bb'], linestyle='--', label='하단 밴드')
    
    # MACD 전략 지표 (시그널 라인)
    elif strategy == 'MACD' and 'macd' in df.columns and 'signal_line' in df.columns:
        # MACD 지표는 별도의 축에 표시하는 것이 좋을 수 있지만, 
        # 여기서는 단순화를 위해 동일 축에 표시
        if 'histogram' in df.columns:
            for i in range(len(df)-1):
                color = colors['histogram_positive'] if df['histogram'].iloc[i] >= 0 else colors['histogram_negative']
                ax.bar(df.index[i], df['histogram'].iloc[i], color=color, alpha=0.3, width=1)
        
        ax.plot(df.index, df['macd'], color=colors['macd'], 
                linewidth=linewidths['ma'], label='MACD')
        ax.plot(df.index, df['signal_line'], color=colors['signal'], 
                linewidth=linewidths['ma'], label='시그널')
    
    # RSI 전략 지표
    elif strategy == 'RSI' and 'rsi' in df.columns:
        # RSI는 일반적으로 0-100 범위의 별도 차트에 표시하는 것이 좋지만,
        # 여기서는 단순화를 위해 표시하지 않음
        pass

def plot_asset_value(
    ax: plt.Axes,
    results_df: pd.DataFrame,
    initial_capital: float,
    style_config: Dict[str, Any]
) -> None:
    """
    자산 가치 차트 그리기
    
    Parameters:
        ax (plt.Axes): matplotlib 축 객체
        results_df (pd.DataFrame): 백테스팅 결과 데이터프레임
        initial_capital (float): 초기 자본금
        style_config (Dict[str, Any]): 스타일 설정
    """
    colors = style_config['colors']
    linewidths = style_config['linewidth']
    alphas = style_config['alpha']
    
    # 로그 스케일 사용 여부 결정 (자산 변화가 크면 로그 스케일 사용)
    use_log_scale = results_df['asset'].max() / results_df['asset'].min() > 5
    
    # 자산 가치 그래프 그리기
    if use_log_scale:
        ax.semilogy(results_df.index, results_df['asset'], color=colors['asset'], 
                   linewidth=linewidths['asset'], label='자산 가치')
        ax.set_ylabel('자산 가치 (로그)', fontsize=style_config['fontsize']['label'])
    else:
        ax.plot(results_df.index, results_df['asset'], color=colors['asset'], 
               linewidth=linewidths['asset'], label='자산 가치')
        ax.set_ylabel('자산 가치', fontsize=style_config['fontsize']['label'])
    
    # 초기 자본금 표시 (기준선)
    ax.axhline(y=initial_capital, color=colors['baseline'], linestyle='--', 
              alpha=alphas['baseline'], label='초기 자본금')
    
    # 차트 설정
    ax.set_title("자산 가치 변화", fontsize=style_config['fontsize']['subtitle'])
    ax.grid(True, alpha=style_config['alpha']['grid'])
    ax.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])

def plot_drawdown(
    ax: plt.Axes,
    results_df: pd.DataFrame,
    style_config: Dict[str, Any]
) -> None:
    """
    드로우다운 차트 그리기
    
    Parameters:
        ax (plt.Axes): matplotlib 축 객체
        results_df (pd.DataFrame): 백테스팅 결과 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
    """
    colors = style_config['colors']
    linewidths = style_config['linewidth']
    alphas = style_config['alpha']
    
    # 드로우다운 영역 채우기
    ax.fill_between(results_df.index, 0, results_df['drawdown'], 
                   color=colors['drawdown'], alpha=alphas['fill'])
    
    # 드로우다운 선 그리기
    ax.plot(results_df.index, results_df['drawdown'], color=colors['drawdown'], 
           linewidth=linewidths['drawdown'])
    
    # 차트 설정
    ax.set_title("드로우다운 (%)", fontsize=style_config['fontsize']['subtitle'])
    ax.set_ylabel('드로우다운 (%)', fontsize=style_config['fontsize']['label'])
    ax.set_ylim(min(results_df['drawdown'].min() * 1.1, -10), 5)  # 최소값 이하로 여유 확보
    ax.grid(True, alpha=style_config['alpha']['grid'])

def plot_performance_summary(
    ax: plt.Axes,
    results: Dict[str, Any],
    style_config: Dict[str, Any]
) -> None:
    """
    백테스팅 성과 요약 텍스트 표시
    
    Parameters:
        ax (plt.Axes): matplotlib 축 객체
        results (Dict[str, Any]): 백테스팅 결과 데이터
        style_config (Dict[str, Any]): 스타일 설정
    """
    # 결과 데이터 추출
    strategy = results.get('strategy', 'Unknown')
    total_return_pct = results['total_return_pct']
    annual_return_pct = results['annual_return_pct']
    max_drawdown_pct = results['max_drawdown_pct']
    trade_count = results['trade_count']
    initial_capital = results['initial_capital']
    final_capital = results['final_capital']
    
    # 요약 텍스트 생성
    summary_text = (
        f"전략 성과 요약 - {strategy}\n\n"
        f"초기 자본금: {initial_capital:,.0f} KRW | 최종 자본금: {final_capital:,.0f} KRW\n"
        f"총 수익률: {total_return_pct:.2f}% | 연간 수익률: {annual_return_pct:.2f}%\n"
        f"최대 낙폭: {max_drawdown_pct:.2f}% | 거래 횟수: {trade_count}\n"
        f"기간: {results['start_date']} ~ {results['end_date']} ({results['total_days']} 일)"
    )
    
    # 텍스트 색상 결정 (수익/손실에 따라)
    text_color = get_color_for_value(total_return_pct, style_config)
    
    # 축 설정
    ax.axis('off')  # 축 숨기기
    
    # 요약 텍스트 표시
    ax.text(0.5, 0.5, summary_text, 
           horizontalalignment='center', 
           verticalalignment='center',
           fontsize=style_config['fontsize']['annotation'], 
           color=text_color, 
           transform=ax.transAxes)

def plot_backtest_results(
    ticker: str, 
    results: Dict[str, Any],
    chart_dir: str = 'backtest_results',
    style: str = 'default'
) -> str:
    """
    백테스팅 결과 차트 생성
    
    Parameters:
        ticker (str): 종목 심볼
        results (Dict[str, Any]): 백테스팅 결과 데이터
        chart_dir (str): 차트 저장 디렉토리
        style (str): 차트 스타일
        
    Returns:
        str: 저장된 차트 파일 경로
    """
    # 스타일 적용
    style_config = apply_style(style)
    
    # 결과 데이터 추출
    df = results['df']
    results_df = results['results_df']
    trade_history = results['trade_history']
    strategy = results.get('strategy', 'Unknown')
    
    # 매수/매도 포인트 추출
    buy_points = [trade['date'] for trade in trade_history if trade['type'] == 'buy']
    sell_points = [trade['date'] for trade in trade_history if trade['type'] == 'sell']
    
    # 그래프 설정
    fig = plt.figure(figsize=style_config['figsize'])
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 1.5, 1.5, 1], hspace=0.15)
    
    # 1. 가격 차트 + 전략
    ax1 = plt.subplot(gs[0])
    
    # 가격 데이터 (로그 스케일 사용)
    ax1.semilogy(df.index, df['close'], color=style_config['colors']['price'], 
                linewidth=style_config['linewidth']['price'], label='가격')
    
    # 전략 지표 그리기 (이동평균선, 볼린저 밴드 등)
    plot_strategy_indicators(ax1, df, strategy, style_config)
    
    # 매수/매도 신호 표시
    plot_trade_signals(ax1, df, buy_points, sell_points, style_config)
    
    # 볼륨 표시 (볼륨 데이터가 있는 경우)
    if 'volume' in df.columns:
        volume_ax = ax1.twinx()
        volume_ax.bar(df.index, df['volume'], color=style_config['colors']['volume'], 
                     alpha=style_config['alpha']['volume'], width=0.8)
        volume_ax.set_ylim(0, df['volume'].max() * 5)
        volume_ax.set_ylabel('거래량', color=style_config['colors']['volume'], 
                            fontsize=style_config['fontsize']['label'])
        volume_ax.tick_params(axis='y', colors=style_config['colors']['volume'])
        volume_ax.grid(False)
    
    # 차트 설정
    strategy_text = f"전략: {strategy}"
    ax1.set_title(f"{ticker} 가격 및 전략 신호\n{strategy_text}", 
                 fontsize=style_config['fontsize']['subtitle'], pad=10)
    ax1.set_ylabel('가격 (로그 스케일)', fontsize=style_config['fontsize']['label'])
    ax1.grid(True, alpha=style_config['alpha']['grid'])
    ax1.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])
    
    # X축 날짜 포맷 설정
    format_date_axis(ax1)
    
    # 2. 자산 변화 그래프
    ax2 = plt.subplot(gs[1], sharex=ax1)
    plot_asset_value(ax2, results_df, results['initial_capital'], style_config)
    
    # 3. 드로우다운 차트
    ax3 = plt.subplot(gs[2], sharex=ax1)
    plot_drawdown(ax3, results_df, style_config)
    
    # 4. 성과 지표 요약
    ax4 = plt.subplot(gs[3])
    plot_performance_summary(ax4, results, style_config)
    
    # X축 데이터 포맷 설정 (중복 날짜 표시 방지)
    for ax in [ax1, ax2, ax3]:
        format_date_axis(ax)
        # 하단 차트(ax3)를 제외한 차트에서는 X축 레이블 숨기기
        if ax != ax3:
            ax.set_xticklabels([])
    
    # 그래프 제목 설정
    plt.suptitle(f"{ticker} 백테스팅 결과 - {strategy} 전략 ({results['start_date']} ~ {results['end_date']})",
                fontsize=style_config['fontsize']['title'], y=0.98)
    
    # 파일 이름 생성 및 저장
    file_name = generate_filename('backtest', ticker, strategy)
    return save_chart(fig, file_name, chart_dir, style_config['dpi'])
