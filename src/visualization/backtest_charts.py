"""
백테스팅 차트 모듈

백테스팅 결과 시각화를 위한 차트 생성 함수를 제공합니다.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
from typing import Dict, List, Tuple, Optional, Any, Union

from src.utils.config import CHART_SAVE_PATH, BACKTEST_CHART_PATH
from src.utils.chart_utils import (
    format_date_axis, format_price_axis, save_chart, generate_filename, 
    setup_chart_dir
)
from src.visualization.styles import apply_style
from src.visualization.viz_helpers import (
    prepare_ohlcv_dataframe, create_chart_title, adjust_figure_size
)
from src.visualization.base_charts import apply_common_chart_style
from src.visualization.indicator_charts import plot_macd, plot_rsi

def get_default_style_config() -> Dict[str, Any]:
    """
    백테스트 차트의 기본 스타일 설정을 반환합니다.
    
    Returns:
        Dict[str, Any]: 스타일 설정 사전
    """
    return {
        'colors': {
            'price': '#1f77b4',  # 파란색
            'buy': '#2ca02c',    # 초록색
            'sell': '#d62728',   # 빨간색
            'portfolio': '#ff7f0e',  # 주황색
            'drawdown': '#d62728',   # 빨간색
            'volume': '#1f77b4',     # 파란색
            'macd': '#1f77b4',      # 파란색
            'signal': '#ff7f0e',    # 주황색
            'histogram': '#2ca02c',  # 초록색
            'overbought': '#d62728', # 빨간색
            'oversold': '#2ca02c',   # 초록색
        },
        'fontsize': {
            'title': 14,
            'subtitle': 12,
            'label': 10,
            'tick': 8,
            'annotation': 9,
        },
        'grid': {
            'alpha': 0.3,
        },
        'figure': {
            'dpi': 100,
        }
    }

def plot_price_data(
    ax: plt.Axes,
    df: pd.DataFrame,
    signals: pd.DataFrame,
    strategy_name: str,
    style_config: Dict[str, Any] = None
) -> None:
    """
    가격 차트와 매수/매도 신호를 그립니다.
    
    Parameters:
        ax (plt.Axes): 그래프를 그릴 축
        df (pd.DataFrame): 가격 데이터프레임
        signals (pd.DataFrame): 매수/매도 신호 데이터프레임
        strategy_name (str): 전략 이름
        style_config (Dict[str, Any]): 스타일 설정
    """
    # 스타일 설정이 없으면 기본값 사용
    if style_config is None:
        style_config = get_default_style_config()
    
    # 가격 차트 그리기
    ax.plot(df.index, df['close'], color=style_config['colors']['price'], linewidth=1.5, label='가격')
    
    # 매수/매도 신호 표시
    if signals is not None and not signals.empty:
        # signals 데이터프레임 형식 확인
        if 'type' in signals.columns:
            # 기존 코드: 'type' 열이 있는 경우
            # 매수 신호
            buy_signals = signals[signals['type'] == 'buy']
            if not buy_signals.empty:
                # 'price' 컬럼이 없으면 'close' 값을 사용
                if 'price' in buy_signals.columns:
                    buy_prices = buy_signals['price']
                else:
                    buy_prices = df.loc[buy_signals.index, 'close'].values
                
                ax.scatter(
                    buy_signals.index, 
                    buy_prices, 
                    color=style_config['colors'].get('buy_signal', '#4CD964'), 
                    marker='^', 
                    s=100, 
                    label='매수'
                )
            
            # 매도 신호
            sell_signals = signals[signals['type'] == 'sell']
            if not sell_signals.empty:
                # 'price' 컬럼이 없으면 'close' 값을 사용
                if 'price' in sell_signals.columns:
                    sell_prices = sell_signals['price']
                else:
                    sell_prices = df.loc[sell_signals.index, 'close'].values
                
                ax.scatter(
                    sell_signals.index, 
                    sell_prices, 
                    color=style_config['colors'].get('sell_signal', '#FF3B30'), 
                    marker='v', 
                    s=100, 
                    label='매도'
                )
        elif 'position' in signals.columns:
            # 'position' 열을 사용하여 매수/매도 신호 표시
            # position 값이 양수이면 매수, 음수이면 매도로 해석
            buy_indices = signals[signals['position'] > 0].index
            sell_indices = signals[signals['position'] < 0].index
            
            if len(buy_indices) > 0:
                buy_prices = df.loc[buy_indices, 'close'].values
                ax.scatter(
                    buy_indices, 
                    buy_prices, 
                    color=style_config['colors'].get('buy_signal', '#4CD964'), 
                    marker='^', 
                    s=100, 
                    label='매수'
                )
            
            if len(sell_indices) > 0:
                sell_prices = df.loc[sell_indices, 'close'].values
                ax.scatter(
                    sell_indices, 
                    sell_prices, 
                    color=style_config['colors'].get('sell_signal', '#FF3B30'), 
                    marker='v', 
                    s=100, 
                    label='매도'
                )
    
    # 텍스트 색상 가져오기
    text_color = style_config.get('colors', {}).get('text', 'white')
    
    # 차트 스타일 적용
    ax.set_title(f'{strategy_name} 백테스팅 결과', fontsize=style_config['fontsize']['title'], color=text_color)
    ax.set_ylabel('가격', fontsize=style_config['fontsize']['label'], color=text_color)
    ax.grid(True, alpha=style_config['grid']['alpha'])
    
    # 범례 스타일 설정
    ax.legend(loc='upper left', facecolor=style_config.get('figure', {}).get('facecolor', '#131722'), 
              edgecolor=text_color, labelcolor=text_color)
    
    # 축 포맷 설정
    format_date_axis(ax)
    format_price_axis(ax)

def plot_backtest_results(
    df: pd.DataFrame,
    signals: pd.DataFrame,
    cash_history: list,
    coin_amount_history: list,
    strategy_name: str,
    save_path: str = None,
    style_config: Dict[str, Any] = None,
    additional_panels: list = None
) -> str:
    """
    백테스트 결과 차트 그리기
    
    Parameters:
        df (pd.DataFrame): 가격 데이터
        signals (pd.DataFrame): 매수/매도 신호
        cash_history (list): 현금 히스토리
        coin_amount_history (list): 코인 수량 히스토리
        strategy_name (str): 전략 이름
        save_path (str): 저장 경로
        style_config (Dict[str, Any]): 스타일 설정
        additional_panels (list): 추가 패널
    
    Returns:
        str: 저장된 차트 파일 경로
    """
    # 스타일 설정
    if style_config is None:
        style_config = get_default_style_config()
    
    # 기본 색상 설정 확인 및 추가
    if 'colors' not in style_config:
        style_config['colors'] = {}
    
    # 필수 색상 키가 없으면 기본값 추가
    default_colors = {
        'portfolio': '#ff7f0e',  # 주황색
        'drawdown': '#d62728',   # 빨간색
        'price': '#1f77b4',      # 파란색
        'text': 'white'          # 흰색
    }
    
    for key, color in default_colors.items():
        if key not in style_config['colors']:
            style_config['colors'][key] = color
    
    # 기본 패널 설정
    if additional_panels is None:
        additional_panels = ['macd', 'rsi', 'portfolio', 'drawdown']
    
    # 패널 수 계산 (기본 1개 + 추가 패널)
    n_panels = 1 + len(additional_panels)
    
    # 패널별 높이 비율 설정 (가격 차트가 가장 큰 비중)
    height_ratios = [3]  # 가격 차트
    for panel in additional_panels:
        if panel in ['macd', 'rsi']:
            height_ratios.append(1.5)  # 기술 지표 패널
        else:
            height_ratios.append(1)  # 포트폴리오, 드로우다운 등
    
    # 배경색 및 테두리색 설정
    facecolor = style_config.get('figure', {}).get('facecolor', '#131722')  # tradingview 스타일 기본값
    edgecolor = style_config.get('figure', {}).get('edgecolor', '#131722')
    
    # 그림 생성
    fig = plt.figure(figsize=(12, 10), facecolor=facecolor, edgecolor=edgecolor)
    
    # 패널(서브플롯) 생성
    gs = gridspec.GridSpec(n_panels, 1, height_ratios=height_ratios)
    axes = []
    for i in range(n_panels):
        axes.append(plt.subplot(gs[i]))
    
    # 패널 인덱스 초기화
    price_ax = axes[0]
    panel_idx = 1
    
    # 가격 패널에 가격 데이터 그리기
    plot_price_data(
        ax=price_ax,
        df=df,
        signals=signals,
        strategy_name=strategy_name,
        style_config=style_config
    )
    
    # 각 서브플롯에 배경색 적용
    for ax in axes:
        ax.set_facecolor(facecolor)
        # 텍스트 색상 설정
        text_color = style_config.get('colors', {}).get('text', 'white')
        ax.tick_params(colors=text_color)
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        for spine in ax.spines.values():
            spine.set_color(text_color)
    
    # 추가 패널 그리기
    for panel in additional_panels:
        if panel_idx >= len(axes):
            print(f"경고: 패널 인덱스({panel_idx})가 범위를 벗어났습니다. 패널 '{panel}'를 그리지 않습니다.")
            break
            
        ax = axes[panel_idx]
        
        # MACD 차트
        if panel == 'macd':
            from src.visualization.indicator_charts import plot_macd
            try:
                plot_macd(ax=ax, df=df, style_config=style_config)
                print("MACD 차트 그리기 완료")
            except Exception as e:
                print(f"MACD 차트 그리기 실패: {e}")
                ax.text(0.5, 0.5, f'MACD 차트 오류: {str(e)}', ha='center', va='center', transform=ax.transAxes)
        
        # RSI 차트
        elif panel == 'rsi':
            from src.visualization.indicator_charts import plot_rsi
            try:
                # RSI 차트 그리기
                print("RSI 차트 그리기 시작")
                plot_rsi(ax=ax, df=df, style_config=style_config)
                print("RSI 차트 그리기 완료")
            except Exception as e:
                print(f"RSI 차트 그리기 실패: {e}")
                ax.text(0.5, 0.5, f'RSI 차트 오류: {str(e)}', ha='center', va='center', transform=ax.transAxes)
        
        # 포트폴리오 가치 차트
        elif panel == 'portfolio':
            try:
                # 자산 가치 계산
                asset_history = []
                for i in range(len(df)):
                    if i < len(cash_history) and i < len(coin_amount_history):
                        price = df['close'].iloc[i]
                        asset = cash_history[i] + coin_amount_history[i] * price
                        asset_history.append(asset)
                
                # 자산 가치 그리기
                if asset_history:
                    asset_series = pd.Series(asset_history, index=df.index[:len(asset_history)])
                    ax.plot(
                        asset_series.index, 
                        asset_series, 
                        color=style_config['colors']['portfolio'], 
                        linewidth=1.5
                    )
                    ax.set_ylabel('포트폴리오 가치', fontsize=style_config.get('fontsize', {}).get('label', 10), color=style_config['colors'].get('text', 'white'))
                    ax.grid(True, alpha=style_config.get('grid', {}).get('alpha', 0.3))
                    print("포트폴리오 차트 그리기 완료")
                else:
                    print("경고: 자산 가치 데이터가 없습니다.")
                    ax.text(0.5, 0.5, '자산 가치 데이터 없음', ha='center', va='center', transform=ax.transAxes)
            except Exception as e:
                print(f"포트폴리오 차트 그리기 실패: {e}")
                ax.text(0.5, 0.5, f'포트폴리오 차트 오류: {str(e)}', ha='center', va='center', transform=ax.transAxes)
        
        # 드로우다운 차트
        elif panel == 'drawdown':
            try:
                # 자산 가치 계산
                asset_history = []
                for i in range(len(df)):
                    if i < len(cash_history) and i < len(coin_amount_history):
                        price = df['close'].iloc[i]
                        asset = cash_history[i] + coin_amount_history[i] * price
                        asset_history.append(asset)
                
                # 드로우다운 계산
                if asset_history:
                    asset_series = pd.Series(asset_history, index=df.index[:len(asset_history)])
                    running_max = asset_series.cummax()
                    drawdown = (asset_series - running_max) / running_max * 100
                    
                    # 드로우다운 그리기
                    ax.fill_between(
                        drawdown.index, 
                        drawdown.values, 
                        0, 
                        color=style_config['colors']['drawdown'], 
                        alpha=0.5
                    )
                    ax.set_ylabel('드로우다운 (%)', fontsize=style_config.get('fontsize', {}).get('label', 10), color=style_config['colors'].get('text', 'white'))
                    ax.grid(True, alpha=style_config.get('grid', {}).get('alpha', 0.3))
                    print("드로우다운 차트 그리기 완료")
                else:
                    print("경고: 자산 가치 데이터가 없습니다.")
                    ax.text(0.5, 0.5, '자산 가치 데이터 없음', ha='center', va='center', transform=ax.transAxes)
            except Exception as e:
                print(f"드로우다운 차트 그리기 실패: {e}")
                ax.text(0.5, 0.5, f'드로우다운 차트 오류: {str(e)}', ha='center', va='center', transform=ax.transAxes)
        
        panel_idx += 1
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 차트 저장
    if save_path:
        print(f"차트 저장 중: {save_path}")
        try:
            # dpi 설정 및 transparent=False로 배경색 보존
            plt.savefig(save_path, dpi=style_config.get('figure', {}).get('dpi', 100), 
                       facecolor=facecolor, edgecolor=edgecolor, transparent=False)
            print(f"차트 저장 완료: {save_path}")
        except Exception as e:
            print(f"차트 저장 실패: {e}")
    
    # 차트 표시를 위한 경로 반환
    return save_path if save_path else ""

def plot_strategy_performance(
    performance_data: Dict[str, Any],
    ticker: str,
    chart_dir: str = BACKTEST_CHART_PATH,
    style: str = 'default'
) -> str:
    """
    전략 성과 요약 차트 생성
    
    Parameters:
        performance_data (Dict[str, Any]): 성과 데이터
        ticker (str): 종목 심볼
        chart_dir (str): 차트 저장 경로
        style (str): 차트 스타일
        
    Returns:
        str: 저장된 차트 파일 경로
    """
    # 스타일 설정
    style_config = apply_style(style)
    
    # 필요한 데이터 추출
    strategy_name = performance_data.get('strategy_name', '전략')
    initial_capital = performance_data.get('initial_capital', 1000000)
    final_capital = performance_data.get('final_capital', initial_capital)
    total_return = performance_data.get('total_return', 0)
    annual_return = performance_data.get('annual_return', 0)
    sharpe_ratio = performance_data.get('sharpe_ratio', 0)
    max_drawdown = performance_data.get('max_drawdown', 0)
    win_rate = performance_data.get('win_rate', 0)
    profit_loss_ratio = performance_data.get('profit_loss_ratio', 0)
    
    # 그림 생성
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [2, 1, 1]})
    
    # 메인 제목
    plt.suptitle(
        f'{ticker} {strategy_name} 전략 성과 요약',
        fontsize=style_config['fontsize']['title'],
        y=0.98
    )
    
    # 패널 1: 자본금 변화 (바 차트)
    labels = ['초기 자본금', '최종 자본금']
    values = [initial_capital, final_capital]
    colors = [style_config['colors'].get('baseline', 'gray'), 
              style_config['colors'].get('profit' if total_return >= 0 else 'loss', 'green')]
    
    bars = ax1.bar(labels, values, color=colors, width=0.5, alpha=0.7)
    
    # 바 위에 값 표시
    for bar in bars:
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width()/2., 
            height * 1.01, 
            f'{height:,.0f} KRW', 
            ha='center', 
            va='bottom', 
            fontsize=style_config['fontsize']['annotation']
        )
    
    # 수익률 텍스트 추가
    if total_return >= 0:
        ax1.text(
            1, 
            initial_capital * 0.5, 
            f'+{total_return:.2f}%', 
            color=style_config['colors'].get('profit', 'green'), 
            fontsize=style_config['fontsize']['annotation'] * 1.5, 
            ha='center', 
            weight='bold'
        )
    else:
        ax1.text(
            1, 
            final_capital * 1.5, 
            f'{total_return:.2f}%', 
            color=style_config['colors'].get('loss', 'red'), 
            fontsize=style_config['fontsize']['annotation'] * 1.5, 
            ha='center', 
            weight='bold'
        )
    
    # 축 설정
    ax1.set_ylabel('자본금 (KRW)', fontsize=style_config['fontsize']['label'])
    ax1.set_title('자본금 변화', fontsize=style_config['fontsize']['subtitle'])
    ax1.grid(axis='y', alpha=0.3)
    
    # 패널 2: 수익률 지표
    metrics1 = ['연간 수익률', '샤프 비율', '최대 손실률']
    values1 = [annual_return, sharpe_ratio, max_drawdown]
    colors1 = [
        style_config['colors'].get('profit' if annual_return >= 0 else 'loss', 'green'),
        style_config['colors'].get('profit' if sharpe_ratio >= 0 else 'loss', 'green'),
        style_config['colors'].get('loss', 'red')
    ]
    
    # 퍼센트 포맷 적용
    formatted_values1 = [
        f'{annual_return:.2f}%',
        f'{sharpe_ratio:.2f}',
        f'{max_drawdown:.2f}%'
    ]
    
    bars1 = ax2.barh(metrics1, [abs(v) for v in values1], color=colors1, alpha=0.7)
    
    # 바 끝에 값 표시
    for i, bar in enumerate(bars1):
        width = bar.get_width()
        ax2.text(
            width * 1.01, 
            bar.get_y() + bar.get_height()/2, 
            formatted_values1[i], 
            va='center', 
            fontsize=style_config['fontsize']['annotation']
        )
    
    # 축 설정
    ax2.set_xlabel('값', fontsize=style_config['fontsize']['label'])
    ax2.set_title('수익률 지표', fontsize=style_config['fontsize']['subtitle'])
    ax2.grid(axis='x', alpha=0.3)
    
    # 패널 3: 거래 지표
    metrics2 = ['승률', '손익비율']
    values2 = [win_rate, profit_loss_ratio]
    colors2 = [
        style_config['colors'].get('profit', 'green'),
        style_config['colors'].get('profit' if profit_loss_ratio >= 1 else 'loss', 'green')
    ]
    
    # 퍼센트 포맷 적용
    formatted_values2 = [
        f'{win_rate:.2f}%',
        f'{profit_loss_ratio:.2f}'
    ]
    
    bars2 = ax3.barh(metrics2, values2, color=colors2, alpha=0.7)
    
    # 바 끝에 값 표시
    for i, bar in enumerate(bars2):
        width = bar.get_width()
        ax3.text(
            width * 1.01, 
            bar.get_y() + bar.get_height()/2, 
            formatted_values2[i], 
            va='center', 
            fontsize=style_config['fontsize']['annotation']
        )
    
    # 축 설정
    ax3.set_xlabel('값', fontsize=style_config['fontsize']['label'])
    ax3.set_title('거래 지표', fontsize=style_config['fontsize']['subtitle'])
    ax3.grid(axis='x', alpha=0.3)
    
    # 레이아웃 조정
    plt.subplots_adjust(top=0.92, bottom=0.08, left=0.1, right=0.95, hspace=0.25)
    
    # 차트 파일 이름 생성 및 저장
    file_name = generate_filename(
        ticker=ticker, 
        suffix=f"{strategy_name}_performance", 
        initial_capital=initial_capital
    )
    
    # dpi 값 확인 및 기본값 설정
    dpi = style_config.get('dpi', 300)
    if isinstance(style_config.get('figure'), dict):
        dpi = style_config['figure'].get('dpi', dpi)
    
    return save_chart(fig, file_name, chart_dir, dpi)

def plot_strategy_comparison(
    results: List[Dict[str, Any]],
    benchmark_data: Optional[pd.DataFrame] = None,
    chart_dir: str = BACKTEST_CHART_PATH,
    style: str = 'default'
) -> str:
    """
    여러 전략의 성과를 비교하는 차트 생성
    
    Parameters:
        results (List[Dict[str, Any]]): 각 전략별 결과 데이터 리스트
        benchmark_data (Optional[pd.DataFrame]): 벤치마크 데이터 (예: BTC 보유)
        chart_dir (str): 차트 저장 경로
        style (str): 차트 스타일
        
    Returns:
        str: 저장된 차트 파일 경로
    """
    if not results:
        print("전략 비교를 위한 결과 데이터가 없습니다.")
        return ""
    
    # 스타일 설정
    style_config = apply_style(style)
    
    # 티커 정보 (첫 번째 결과에서 가져옴)
    ticker = results[0].get('ticker', 'unknown')
    
    # 그림 생성
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
    
    # 메인 제목
    plt.suptitle(
        f'{ticker} 전략 성과 비교',
        fontsize=style_config['fontsize']['title'],
        y=0.98
    )
    
    # 패널 1: 수익률 비교
    strategy_names = []
    returns = []
    annual_returns = []
    colors = []
    
    for i, result in enumerate(results):
        strategy_name = result.get('strategy_name', f'전략 {i+1}')
        total_return = result.get('total_return', 0)
        annual_return = result.get('annual_return', 0)
        
        strategy_names.append(strategy_name)
        returns.append(total_return)
        annual_returns.append(annual_return)
        
        # 색상 설정 (수익/손실에 따라)
        colors.append(style_config['colors'].get(
            'profit' if total_return >= 0 else 'loss', 
            'green' if total_return >= 0 else 'red'
        ))
    
    # 벤치마크 데이터가 있으면 추가
    if benchmark_data is not None and 'return' in benchmark_data:
        strategy_names.append('Buy & Hold')
        returns.append(benchmark_data['return'])
        annual_returns.append(benchmark_data.get('annual_return', 0))
        colors.append(style_config['colors'].get('baseline', 'gray'))
    
    # 수익률 바 차트
    bars1 = ax1.bar(strategy_names, returns, color=colors, alpha=0.7)
    
    # 바 위에 값 표시
    for bar in bars1:
        height = bar.get_height()
        color = 'green' if height >= 0 else 'red'
        va = 'bottom' if height >= 0 else 'top'
        ax1.text(
            bar.get_x() + bar.get_width()/2, 
            height * (1.01 if height >= 0 else 0.99), 
            f'{height:.2f}%', 
            ha='center', 
            va=va, 
            color=color, 
            fontsize=style_config['fontsize']['annotation']
        )
    
    # 0% 기준선
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # 축 설정
    ax1.set_ylabel('총 수익률 (%)', fontsize=style_config['fontsize']['label'])
    ax1.set_title('전략별 총 수익률 비교', fontsize=style_config['fontsize']['subtitle'])
    ax1.grid(axis='y', alpha=0.3)
    
    # 패널 2: 연간 수익률 및 샤프 비율
    x = np.arange(len(strategy_names))
    width = 0.35
    
    # 연간 수익률 바 차트
    bars2 = ax2.bar(
        x - width/2, 
        annual_returns, 
        width, 
        color=[style_config['colors'].get('profit', 'green') if r >= 0 else 
              style_config['colors'].get('loss', 'red') for r in annual_returns], 
        alpha=0.7, 
        label='연간 수익률'
    )
    
    # 샤프 비율 추출 및 바 차트
    sharpe_ratios = [result.get('sharpe_ratio', 0) for result in results]
    if benchmark_data is not None:
        sharpe_ratios.append(benchmark_data.get('sharpe_ratio', 0))
    
    bars3 = ax2.bar(
        x + width/2, 
        sharpe_ratios, 
        width, 
        color=style_config['colors'].get('macd', 'blue'), 
        alpha=0.7, 
        label='샤프 비율'
    )
    
    # 바 위에 값 표시
    for bar in bars2:
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width()/2, 
            height * (1.01 if height >= 0 else 0.99), 
            f'{height:.2f}%', 
            ha='center', 
            va='bottom' if height >= 0 else 'top', 
            fontsize=style_config['fontsize']['annotation'] * 0.8
        )
    
    for bar in bars3:
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width()/2, 
            height * (1.01 if height >= 0 else 0.99), 
            f'{height:.2f}', 
            ha='center', 
            va='bottom' if height >= 0 else 'top', 
            fontsize=style_config['fontsize']['annotation'] * 0.8
        )
    
    # 0 기준선
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # 축 설정
    ax2.set_ylabel('값', fontsize=style_config['fontsize']['label'])
    ax2.set_title('연간 수익률 및 샤프 비율 비교', fontsize=style_config['fontsize']['subtitle'])
    ax2.set_xticks(x)
    ax2.set_xticklabels(strategy_names, rotation=0, ha='center')
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    # 레이아웃 조정
    plt.subplots_adjust(top=0.92, bottom=0.08, left=0.1, right=0.95, hspace=0.25)
    
    # 차트 파일 이름 생성 및 저장
    file_name = generate_filename(
        ticker=ticker, 
        suffix=f"strategy_comparison_{len(results)}"
    )
    
    # dpi 값 확인 및 기본값 설정
    dpi = style_config.get('dpi', 300)
    if isinstance(style_config.get('figure'), dict):
        dpi = style_config['figure'].get('dpi', dpi)
    
    return save_chart(fig, file_name, chart_dir, dpi) 