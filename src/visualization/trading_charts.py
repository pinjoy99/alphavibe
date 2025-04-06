"""
트레이딩 차트 모듈

거래 및 계좌 정보 시각화에 사용되는 차트를 생성하는 함수를 제공합니다.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime

from src.utils.config import CHART_SAVE_PATH
from src.utils.chart_utils import save_chart, setup_chart_dir
from src.visualization.styles import apply_style
from src.visualization.viz_helpers import add_colormap_to_values

def plot_asset_distribution(
    summary: Dict[str, Any], 
    chart_dir: Optional[str] = None,
    style: str = 'tradingview'
) -> str:
    """
    자산 분포 파이 차트 생성
    
    Parameters:
        summary (Dict[str, Any]): 계좌 요약 정보
        chart_dir (str, optional): 차트 저장 디렉토리
        style (str): 차트 스타일
        
    Returns:
        str: 저장된 차트 경로
    """
    # 차트 디렉토리 설정
    if chart_dir is None:
        chart_dir = setup_chart_dir(CHART_SAVE_PATH)
    
    # 스타일 설정
    style_config = apply_style(style)
    
    # 현재 시간
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 데이터 준비
    labels = ['KRW']
    values = [summary['total_krw']]
    
    # 색상 팔레트
    colors = [style_config['colors'].get('currency', '#00FFFF')]  # KRW는 시안색
    
    # 코인 정보 추가
    for i, coin in enumerate(summary.get('coins', [])):
        if coin.get('current_value', 0) > 0:
            labels.append(coin.get('currency', f'코인 {i+1}'))
            values.append(coin.get('current_value', 0))
            
    # 나머지 색상 설정
    if len(values) > 1:
        coin_colors = []
        for i in range(1, len(values)):
            color_idx = i % len(style_config.get('color_palette', ['#FF5733', '#33FF57', '#3357FF', '#FF33A8', '#FFD133']))
            if 'color_palette' in style_config:
                coin_colors.append(style_config['color_palette'][color_idx])
            else:
                # 기본 색상 목록
                default_colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33A8', '#FFD133']
                coin_colors.append(default_colors[color_idx])
        colors.extend(coin_colors)
    
    # 소액 코인 추가 (others)
    others = summary.get('others', {})
    if others.get('total_value', 0) > 0:
        labels.append('기타 코인')
        values.append(others.get('total_value', 0))
        colors.append('#AAAAAA')  # 회색
    
    # 파이 차트 생성
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 제목 설정
    plt.title(f'자산 분포 ({now})', fontsize=style_config['fontsize']['title'])
    
    # 값이 너무 작은 항목은 따로 그룹화 (전체의 1% 미만)
    threshold = summary.get('total_asset_value', sum(values)) * 0.01
    small_values_sum = 0
    filtered_labels = []
    filtered_values = []
    filtered_colors = []
    
    for i, value in enumerate(values):
        if value >= threshold:
            filtered_labels.append(labels[i])
            filtered_values.append(value)
            filtered_colors.append(colors[i])
        else:
            small_values_sum += value
    
    # 작은 값들을 하나의 항목으로 합침
    if small_values_sum > 0:
        filtered_labels.append('기타 (<1%)')
        filtered_values.append(small_values_sum)
        filtered_colors.append('#AAAAAA')  # 회색
    
    # 총 자산이 0이면 빈 차트 생성
    if sum(filtered_values) <= 0:
        plt.text(0.5, 0.5, '자산 정보 없음', ha='center', va='center', fontsize=14)
    else:
        # 파이 차트 그리기
        wedges, texts, autotexts = plt.pie(
            filtered_values, 
            labels=filtered_labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=filtered_colors,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
            textprops={'fontsize': style_config['fontsize']['label'], 'color': style_config['colors'].get('text', 'black')}
        )
        
        # 자동 텍스트 속성 설정
        plt.setp(autotexts, fontsize=style_config['fontsize']['annotation'], fontweight='bold')
        
        # 원 가운데에 총 자산 표시
        plt.text(0, 0, f"총 자산가치\n{summary.get('total_asset_value', sum(filtered_values)):,.0f} KRW", 
                ha='center', va='center', fontsize=style_config['fontsize']['subtitle'], fontweight='bold')
        
        # 범례 표시
        plt.legend(
            title='자산 구성',
            title_fontsize=style_config['fontsize']['legend'],
            loc='upper right',
            bbox_to_anchor=(1, 0.9),
            fontsize=style_config['fontsize']['annotation']
        )
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 차트 저장
    chart_filename = f"asset_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    chart_path = os.path.join(chart_dir, chart_filename)
    plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
    plt.close()
    
    return chart_path

def plot_profit_loss(
    summary: Dict[str, Any], 
    chart_dir: Optional[str] = None,
    style: str = 'tradingview'
) -> str:
    """
    코인별 손익 차트 생성
    
    Parameters:
        summary (Dict[str, Any]): 계좌 요약 정보
        chart_dir (str, optional): 차트 저장 디렉토리
        style (str): 차트 스타일
        
    Returns:
        str: 저장된 차트 경로
    """
    # 차트 디렉토리 설정
    if chart_dir is None:
        chart_dir = setup_chart_dir(CHART_SAVE_PATH)
    
    # 스타일 설정
    style_config = apply_style(style)
    
    # 현재 시간
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 데이터 준비
    coins = []
    profit_loss = []
    profit_loss_pct = []
    
    # 의미 있는 금액의 코인만 포함 (1,000원 이상 손익)
    min_profit_threshold = 1000.0
    
    # 코인 정보 추가 (손익 절대값 기준 정렬)
    sorted_coins = sorted(
        summary.get('coins', []), 
        key=lambda x: abs(x.get('profit_loss', 0)), 
        reverse=True
    )
    
    for coin in sorted_coins:
        if coin.get('invested_value', 0) > 0 and abs(coin.get('profit_loss', 0)) >= min_profit_threshold:
            coins.append(coin.get('currency', 'unknown'))
            profit_loss.append(coin.get('profit_loss', 0))
            profit_loss_pct.append(coin.get('profit_loss_pct', 0))
    
    # 그래프 생성
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [1.5, 1]})
    
    # 메인 제목
    plt.suptitle(f'코인별 손익 현황 ({now})', fontsize=style_config['fontsize']['title'])
    
    # 차트가 비어있으면 빈 차트 생성 후 반환
    if not coins:
        plt.figtext(0.5, 0.5, '표시할 손익이 없습니다.', ha='center', va='center', fontsize=style_config['fontsize']['subtitle'])
        
        # 차트 저장
        chart_filename = f"profit_loss_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        chart_path = os.path.join(chart_dir, chart_filename)
        plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    # 최대 표시할 코인 개수 제한 (너무 많으면 가독성 저하)
    max_display_coins = 10
    if len(coins) > max_display_coins:
        # 상위 n개 코인만 유지
        coins = coins[:max_display_coins]
        profit_loss = profit_loss[:max_display_coins]
        profit_loss_pct = profit_loss_pct[:max_display_coins]
    
    # 패널 1: 절대 손익
    # 색상 설정 (이익은 초록색, 손실은 빨간색)
    colors = [
        style_config['colors'].get('profit', 'green') if p >= 0 else 
        style_config['colors'].get('loss', 'red') 
        for p in profit_loss
    ]
    
    # 바 차트 그리기
    bars1 = ax1.barh(coins, profit_loss, color=colors, alpha=0.7)
    
    # 바 위에 값 표시
    for bar in bars1:
        width = bar.get_width()
        ax1.text(
            width * (1.01 if width >= 0 else 0.99), 
            bar.get_y() + bar.get_height()/2, 
            f'{width:,.0f} KRW', 
            ha='left' if width >= 0 else 'right', 
            va='center', 
            fontsize=style_config['fontsize']['annotation']
        )
    
    # 0 라인 추가
    ax1.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # 축 제목 및 설정
    ax1.set_title('코인별 절대 손익', fontsize=style_config['fontsize']['subtitle'])
    ax1.set_xlabel('손익 (KRW)', fontsize=style_config['fontsize']['label'])
    ax1.grid(axis='x', alpha=0.3)
    
    # 패널 2: 상대 손익 (%)
    # 색상 설정
    colors_pct = [
        style_config['colors'].get('profit', 'green') if p >= 0 else 
        style_config['colors'].get('loss', 'red') 
        for p in profit_loss_pct
    ]
    
    # 바 차트 그리기
    bars2 = ax2.barh(coins, profit_loss_pct, color=colors_pct, alpha=0.7)
    
    # 바 위에 값 표시
    for bar in bars2:
        width = bar.get_width()
        ax2.text(
            width * (1.01 if width >= 0 else 0.99), 
            bar.get_y() + bar.get_height()/2, 
            f'{width:.2f}%', 
            ha='left' if width >= 0 else 'right', 
            va='center', 
            fontsize=style_config['fontsize']['annotation']
        )
    
    # 0 라인 추가
    ax2.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # 축 제목 및 설정
    ax2.set_title('코인별 상대 손익 (%)', fontsize=style_config['fontsize']['subtitle'])
    ax2.set_xlabel('손익률 (%)', fontsize=style_config['fontsize']['label'])
    ax2.grid(axis='x', alpha=0.3)
    
    # 레이아웃 조정
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # 차트 저장
    chart_filename = f"profit_loss_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    chart_path = os.path.join(chart_dir, chart_filename)
    plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
    plt.close()
    
    return chart_path

def plot_trade_history(
    trade_history: pd.DataFrame,
    ticker: Optional[str] = None,
    chart_dir: Optional[str] = None,
    style: str = 'default',
    limit: int = 30
) -> str:
    """
    거래 내역 시각화
    
    Parameters:
        trade_history (pd.DataFrame): 거래 내역 데이터프레임
        ticker (str, optional): 특정 티커만 필터링 (None이면 모든 티커)
        chart_dir (str, optional): 차트 저장 디렉토리
        style (str): 차트 스타일
        limit (int): 최대 표시 거래 수
        
    Returns:
        str: 저장된 차트 경로
    """
    # 차트 디렉토리 설정
    if chart_dir is None:
        chart_dir = setup_chart_dir(CHART_SAVE_PATH)
    
    # 스타일 설정
    style_config = apply_style(style)
    
    # 거래 내역이 비어있는지 확인
    if trade_history.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        plt.text(0.5, 0.5, '거래 내역이 없습니다.', ha='center', va='center', fontsize=style_config['fontsize']['subtitle'])
        
        # 차트 저장
        chart_filename = f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        chart_path = os.path.join(chart_dir, chart_filename)
        plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    # 데이터 전처리
    # 필수 컬럼 확인 및 생성
    required_cols = ['timestamp', 'type', 'ticker', 'price', 'quantity', 'total']
    for col in required_cols:
        if col not in trade_history.columns:
            if col == 'total' and 'price' in trade_history.columns and 'quantity' in trade_history.columns:
                trade_history['total'] = trade_history['price'] * trade_history['quantity']
            else:
                trade_history[col] = None
    
    # 특정 티커만 필터링
    if ticker:
        filtered_df = trade_history[trade_history['ticker'] == ticker].copy()
        if filtered_df.empty:
            filtered_df = trade_history.copy()
            print(f"경고: {ticker} 티커에 대한 거래 내역이 없습니다. 모든 거래를 표시합니다.")
    else:
        filtered_df = trade_history.copy()
    
    # 최신 거래부터 내림차순 정렬
    filtered_df = filtered_df.sort_values(by='timestamp', ascending=False)
    
    # 최대 표시 개수 제한
    display_df = filtered_df.head(limit)
    
    # 타임스탬프가 datetime 형식인지 확인
    if display_df['timestamp'].dtype != 'datetime64[ns]':
        try:
            display_df['timestamp'] = pd.to_datetime(display_df['timestamp'])
        except:
            pass
    
    # 날짜 형식 변환
    display_df['formatted_date'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    
    # 그래프 설정
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # 거래 유형별 색상 설정
    type_colors = {
        'buy': style_config['colors'].get('buy_signal', 'green'),
        'sell': style_config['colors'].get('sell_signal', 'red'),
        'deposit': style_config['colors'].get('deposit', 'blue'),
        'withdraw': style_config['colors'].get('withdraw', 'purple')
    }
    
    # 거래 데이터 추출
    dates = display_df['formatted_date'].values
    tickers = display_df['ticker'].values
    types = display_df['type'].values
    prices = display_df['price'].values
    quantities = display_df['quantity'].values
    totals = display_df['total'].values
    
    # 표 데이터 생성
    table_data = []
    for i in range(len(display_df)):
        price_str = f"{prices[i]:,.0f}" if not pd.isna(prices[i]) else "-"
        quantity_str = f"{quantities[i]:.8f}" if not pd.isna(quantities[i]) else "-"
        total_str = f"{totals[i]:,.0f}" if not pd.isna(totals[i]) else "-"
        
        row = [dates[i], tickers[i], types[i].upper(), price_str, quantity_str, total_str]
        table_data.append(row)
    
    # 표 컬럼
    columns = ['날짜', '코인', '유형', '가격 (KRW)', '수량', '총액 (KRW)']
    
    # 색상 설정
    cell_colors = []
    for i in range(len(display_df)):
        type_color = type_colors.get(types[i].lower(), 'gray')
        color_alpha = [(*plt.matplotlib.colors.to_rgb(type_color), 0.2)]  # 타입 컬럼에만 색상 적용
        row_color = ['white'] * 2 + color_alpha + ['white'] * 3
        cell_colors.append(row_color)
    
    # 표 생성
    table = ax.table(
        cellText=table_data,
        colLabels=columns,
        cellLoc='center',
        loc='center',
        cellColours=cell_colors
    )
    
    # 표 스타일 설정
    table.auto_set_font_size(False)
    table.set_fontsize(style_config['fontsize']['annotation'])
    table.scale(1, 1.5)  # 행 높이 조정
    
    # 축 숨기기
    ax.axis('off')
    
    # 제목 설정
    ticker_str = f' - {ticker}' if ticker else ''
    plt.title(f'최근 거래 내역{ticker_str} ({len(display_df)}건)', fontsize=style_config['fontsize']['title'])
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 차트 저장
    ticker_suffix = f"_{ticker}" if ticker else ""
    chart_filename = f"trade_history{ticker_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    chart_path = os.path.join(chart_dir, chart_filename)
    plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
    plt.close()
    
    return chart_path

def plot_portfolio_history(
    portfolio_history: pd.DataFrame,
    chart_dir: Optional[str] = None,
    style: str = 'default',
    period: str = '1m'
) -> str:
    """
    포트폴리오 자산 가치 변화 차트 생성
    
    Parameters:
        portfolio_history (pd.DataFrame): 자산 가치 변화 이력 데이터프레임
        chart_dir (str, optional): 차트 저장 디렉토리
        style (str): 차트 스타일
        period (str): 표시 기간
        
    Returns:
        str: 저장된 차트 경로
    """
    # 차트 디렉토리 설정
    if chart_dir is None:
        chart_dir = setup_chart_dir(CHART_SAVE_PATH)
    
    # 스타일 설정
    style_config = apply_style(style)
    
    # 데이터가 비어있는지 확인
    if portfolio_history.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        plt.text(0.5, 0.5, '포트폴리오 이력이 없습니다.', ha='center', va='center', fontsize=style_config['fontsize']['subtitle'])
        
        # 차트 저장
        chart_filename = f"portfolio_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        chart_path = os.path.join(chart_dir, chart_filename)
        plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    # 인덱스가 datetime 타입인지 확인
    if not isinstance(portfolio_history.index, pd.DatetimeIndex):
        try:
            portfolio_history.index = pd.to_datetime(portfolio_history.index)
        except:
            # 인덱스를 datetime으로 변환할 수 없는 경우
            portfolio_history = portfolio_history.reset_index()
            if 'timestamp' in portfolio_history.columns:
                portfolio_history['timestamp'] = pd.to_datetime(portfolio_history['timestamp'])
                portfolio_history = portfolio_history.set_index('timestamp')
            elif 'date' in portfolio_history.columns:
                portfolio_history['date'] = pd.to_datetime(portfolio_history['date'])
                portfolio_history = portfolio_history.set_index('date')
    
    # 그래프 설정
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
    
    # 메인 제목
    plt.suptitle(f'포트폴리오 가치 변화 ({period})', fontsize=style_config['fontsize']['title'])
    
    # 패널 1: 자산 가치 변화
    total_value_col = None
    # 총 자산 가치 컬럼 찾기
    for col in ['total_value', 'portfolio_value', 'asset_value', 'total_asset_value']:
        if col in portfolio_history.columns:
            total_value_col = col
            break
    
    if total_value_col:
        # 자산 가치 그리기
        ax1.plot(
            portfolio_history.index, 
            portfolio_history[total_value_col], 
            color=style_config['colors'].get('asset', 'green'), 
            linewidth=2, 
            label='총 자산 가치'
        )
        
        # 시작 포인트 표시
        ax1.scatter(
            portfolio_history.index[0], 
            portfolio_history[total_value_col].iloc[0], 
            color=style_config['colors'].get('ma_short', 'blue'), 
            s=100, 
            zorder=5, 
            label='시작'
        )
        
        # 마지막 포인트 표시
        ax1.scatter(
            portfolio_history.index[-1], 
            portfolio_history[total_value_col].iloc[-1], 
            color=style_config['colors'].get('macd', 'purple'), 
            s=100, 
            zorder=5, 
            label='현재'
        )
        
        # 원화/코인 분리 (있는 경우)
        if 'krw_value' in portfolio_history.columns:
            ax1.fill_between(
                portfolio_history.index,
                0,
                portfolio_history['krw_value'],
                color=style_config['colors'].get('currency', 'skyblue'),
                alpha=0.5,
                label='KRW'
            )
            
            if 'coin_value' in portfolio_history.columns:
                ax1.fill_between(
                    portfolio_history.index,
                    portfolio_history['krw_value'],
                    portfolio_history[total_value_col],
                    color=style_config['colors'].get('profit', 'lightgreen'),
                    alpha=0.5,
                    label='코인'
                )
        
        # 축 설정
        ax1.set_ylabel('자산 가치 (KRW)', fontsize=style_config['fontsize']['label'])
        ax1.set_title('총 자산 가치 변화', fontsize=style_config['fontsize']['subtitle'])
        ax1.legend(loc='best', fontsize=style_config['fontsize']['legend'])
        ax1.grid(True, alpha=0.3)
        
        # 천 단위 콤마
        ax1.yaxis.set_major_formatter(plt.matplotlib.ticker.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
        
        # 패널 2: 일일 변화 및 수익률
        if 'daily_change_pct' in portfolio_history.columns:
            change_col = 'daily_change_pct'
        else:
            # 일일 변화율 계산
            portfolio_history['daily_change_pct'] = portfolio_history[total_value_col].pct_change() * 100
            change_col = 'daily_change_pct'
        
        # 바 차트 색상 (양수/음수)
        colors = np.where(
            portfolio_history[change_col] >= 0, 
            style_config['colors'].get('profit', 'green'), 
            style_config['colors'].get('loss', 'red')
        )
        
        # 일일 변화율 바 차트
        ax2.bar(
            portfolio_history.index, 
            portfolio_history[change_col], 
            color=colors, 
            alpha=0.7, 
            width=0.8
        )
        
        # 0% 라인
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # 축 설정
        ax2.set_ylabel('일일 변화율 (%)', fontsize=style_config['fontsize']['label'])
        ax2.set_title('일일 수익률', fontsize=style_config['fontsize']['subtitle'])
        ax2.grid(True, alpha=0.3)
    else:
        # 총 자산 가치 컬럼이 없는 경우, 사용 가능한 컬럼 찾아 그리기
        for col in portfolio_history.columns:
            if col.lower() not in ['index', 'date', 'timestamp']:
                ax1.plot(
                    portfolio_history.index, 
                    portfolio_history[col], 
                    linewidth=2, 
                    label=col
                )
        
        ax1.set_ylabel('값', fontsize=style_config['fontsize']['label'])
        ax1.set_title('포트폴리오 이력', fontsize=style_config['fontsize']['subtitle'])
        ax1.legend(loc='best', fontsize=style_config['fontsize']['legend'])
        ax1.grid(True, alpha=0.3)
        
        # 패널 2: 비어있음 표시
        ax2.text(0.5, 0.5, '일일 변화 데이터 없음', ha='center', va='center', fontsize=style_config['fontsize']['annotation'])
        ax2.axis('off')
    
    # x축 포맷 설정
    ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
    ax2.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
    
    fig.autofmt_xdate()  # 날짜 라벨 회전
    
    # 레이아웃 조정
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # 차트 저장
    chart_filename = f"portfolio_history_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    chart_path = os.path.join(chart_dir, chart_filename)
    plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
    plt.close()
    
    return chart_path 