import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import os
from datetime import datetime
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates

from .styles import set_chart_style, COLORS
from .utils import setup_chart_dir, save_chart

def plot_asset_distribution(summary: Dict[str, Any], chart_dir: Optional[str] = None) -> str:
    """
    자산 분포 파이 차트 생성 (개선된 버전)
    
    Parameters:
        summary (Dict[str, Any]): 계좌 요약 정보
        chart_dir (str, optional): 차트 저장 디렉토리
        
    Returns:
        str: 저장된 차트 경로
    """
    # 차트 디렉토리 설정
    if chart_dir is None:
        chart_dir = setup_chart_dir('results/account')
    
    # 스타일 설정
    set_chart_style('dark_background')
    
    # 현재 시간
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 데이터 준비
    labels = ['KRW']
    values = [summary['total_krw']]
    colors = ['#00FFFF']  # KRW는 시안색
    
    # 코인 정보 추가
    for i, coin in enumerate(summary['coins']):
        if coin['current_value'] > 0:
            labels.append(coin['currency'])
            values.append(coin['current_value'])
            # 색상 할당 (코인별로 다른 색상)
            color_idx = i % len(COLORS)
            colors.append(COLORS[color_idx])
    
    # 소액 코인 추가 (others)
    others = summary.get('others', {})
    if others.get('total_value', 0) > 0:
        labels.append('기타 코인')
        values.append(others.get('total_value', 0))
        colors.append('#AAAAAA')  # 회색
    
    # 파이 차트 생성
    plt.figure(figsize=(10, 8))
    
    # 제목 설정
    plt.title(f'자산 분포 ({now})', fontsize=16)
    
    # 값이 너무 작은 항목은 따로 그룹화 (전체의 1% 미만)
    threshold = summary['total_asset_value'] * 0.01
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
            textprops={'fontsize': 12, 'color': 'white'}
        )
        
        # 자동 텍스트 속성 설정
        plt.setp(autotexts, fontsize=10, fontweight='bold')
        
        # 원 가운데에 총 자산 표시
        plt.text(0, 0, f"총 자산가치\n{summary['total_asset_value']:,.0f} KRW", 
                ha='center', va='center', fontsize=14, fontweight='bold')
        
        # 범례 표시
        plt.legend(
            title='자산 구성',
            title_fontsize=12,
            loc='upper right',
            bbox_to_anchor=(1, 0.9),
            fontsize=10
        )
    
    # 레이아웃 조정
    plt.tight_layout()
    
    # 차트 저장
    chart_filename = f"asset_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    chart_path = os.path.join(chart_dir, chart_filename)
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return chart_path

def plot_profit_loss(summary: Dict[str, Any], chart_dir: Optional[str] = None) -> str:
    """
    코인별 손익 차트 생성 (개선된 버전)
    
    Parameters:
        summary (Dict[str, Any]): 계좌 요약 정보
        chart_dir (str, optional): 차트 저장 디렉토리
        
    Returns:
        str: 저장된 차트 경로
    """
    # 차트 디렉토리 설정
    if chart_dir is None:
        chart_dir = setup_chart_dir('results/account')
    
    # 스타일 설정
    set_chart_style('dark_background')
    
    # 현재 시간
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 데이터 준비
    coins = []
    profit_loss = []
    profit_loss_pct = []
    colors = []
    
    # 의미 있는 금액의 코인만 포함 (1,000원 이상 손익)
    min_profit_threshold = 1000.0
    
    # 코인 정보 추가 (손익 절대값 기준 정렬)
    sorted_coins = sorted(summary['coins'], key=lambda x: abs(x['profit_loss']), reverse=True)
    
    for coin in sorted_coins:
        if coin['invested_value'] > 0 and abs(coin['profit_loss']) >= min_profit_threshold:
            coins.append(coin['currency'])
            profit_loss.append(coin['profit_loss'])
            profit_loss_pct.append(coin['profit_loss_pct'])
            # 색상 설정 (이익은 초록색, 손실은 빨간색)
            if coin['profit_loss'] >= 0:
                colors.append('#00FF00')  # 초록색
            else:
                colors.append('#FF0000')  # 빨간색
    
    # 차트가 비어있으면 빈 차트 생성 후 반환
    if not coins:
        plt.figure(figsize=(10, 6))
        plt.title('코인별 손익 현황 (표시할 손익 없음)', fontsize=16)
        plt.text(0.5, 0.5, '의미 있는 손익이 없습니다.', ha='center', va='center', fontsize=14)
        
        # 차트 저장
        chart_filename = f"profit_loss_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        chart_path = os.path.join(chart_dir, chart_filename)
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    # 최대 표시할 코인 개수 제한 (너무 많으면 가독성 저하)
    max_display_coins = 10
    if len(coins) > max_display_coins:
        # 하위 코인들을 '기타'로 통합
        other_profit_loss = sum(profit_loss[max_display_coins:])
        other_invested = sum(coin['invested_value'] for coin in sorted_coins[max_display_coins:] 
                          if abs(coin['profit_loss']) >= min_profit_threshold)
        
        if other_invested > 0:
            other_profit_loss_pct = (other_profit_loss / other_invested) * 100
        else:
            other_profit_loss_pct = 0
            
        # 상위 코인만 유지하고 '기타' 추가
        coins = coins[:max_display_coins] + ['기타']
        profit_loss = profit_loss[:max_display_coins] + [other_profit_loss]
        profit_loss_pct = profit_loss_pct[:max_display_coins] + [other_profit_loss_pct]
        
        # 색상 추가
        other_color = '#00FF00' if other_profit_loss >= 0 else '#FF0000'
        colors = colors[:max_display_coins] + [other_color]
    
    # 2개의 서브플롯 생성 (금액, 퍼센트)
    fig = plt.figure(figsize=(12, 10))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.5, 1])
    
    # 금액 기준 차트
    ax1 = plt.subplot(gs[0])
    bars1 = ax1.bar(coins, profit_loss, color=colors)
    ax1.set_title(f'코인별 손익 금액 ({now})', fontsize=16)
    ax1.set_ylabel('손익 (KRW)', fontsize=12)
    ax1.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    
    # 막대 위에 값 표시
    for bar in bars1:
        height = bar.get_height()
        if height >= 0:
            va = 'bottom'
            y_offset = max(abs(height) * 0.01, 0.5)
        else:
            va = 'top'
            y_offset = -max(abs(height) * 0.01, 0.5)
        
        # +/- 부호 추가
        value_str = f"+{height:,.0f}" if height >= 0 else f"{height:,.0f}"
        
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            height + y_offset,
            value_str,
            ha='center',
            va=va,
            fontsize=9
        )
    
    # x축 레이블 회전 (코인이 많을 경우 가독성 향상)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
    
    # 퍼센트 기준 차트
    ax2 = plt.subplot(gs[1])
    bars2 = ax2.bar(coins, profit_loss_pct, color=colors)
    ax2.set_title('코인별 손익률 (%)', fontsize=16)
    ax2.set_ylabel('손익률 (%)', fontsize=12)
    ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    
    # 막대 위에 값 표시
    for bar in bars2:
        height = bar.get_height()
        if height >= 0:
            va = 'bottom'
            y_offset = max(abs(height) * 0.05, 0.5)
        else:
            va = 'top'
            y_offset = -max(abs(height) * 0.05, 0.5)
            
        # +/- 부호 추가
        value_str = f"+{height:.2f}%" if height >= 0 else f"{height:.2f}%"
        
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            height + y_offset,
            value_str,
            ha='center',
            va=va,
            fontsize=9
        )
    
    # x축 레이블 회전 (코인이 많을 경우 가독성 향상)
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    
    # 전체 수익률 정보 추가
    total_profit_loss = summary.get('total_profit_loss', 0)
    profit_sign = "+" if total_profit_loss >= 0 else ""
    
    plt.figtext(
        0.5, 0.02,
        f"총 손익: {profit_sign}{total_profit_loss:,.0f} KRW ({profit_sign}{summary.get('total_profit_loss_pct', 0):.2f}%)",
        ha='center',
        fontsize=12,
        bbox=dict(facecolor='#333333', alpha=0.6, edgecolor='#CCCCCC', boxstyle='round,pad=0.5')
    )
    
    # 레이아웃 조정
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3, bottom=0.15)
    
    # 차트 저장
    chart_filename = f"profit_loss_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    chart_path = os.path.join(chart_dir, chart_filename)
    plt.savefig(chart_path, dpi=100, bbox_inches='tight')
    plt.close()
    
    return chart_path 