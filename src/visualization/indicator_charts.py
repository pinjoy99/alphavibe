"""
지표 차트 모듈

기술 지표 시각화를 위한 차트 생성 함수를 제공합니다.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.figure import Figure
from typing import Dict, List, Tuple, Optional, Any, Union

from src.utils.config import CHART_SAVE_PATH
from src.utils.chart_utils import (
    save_chart, setup_chart_dir, format_date_axis, 
    format_price_axis, generate_filename
)
from src.visualization.styles import apply_style
from src.visualization.viz_helpers import (
    prepare_ohlcv_dataframe, add_colormap_to_values, create_chart_title
)

def plot_macd(
    ax: plt.Axes, 
    df: pd.DataFrame, 
    style_config: Dict[str, Any],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    show_legend: bool = True
) -> None:
    """
    MACD 차트 그리기
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
        fast_period (int): 단기 EMA 기간
        slow_period (int): 장기 EMA 기간
        signal_period (int): 신호선 기간
        show_legend (bool): 범례 표시 여부
        
    Returns:
        None
    """
    # 데이터프레임이 비어있는지 확인
    if df is None or df.empty:
        ax.text(0.5, 0.5, 'MACD 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 가격 컬럼 찾기 (대소문자 처리)
    price_col = None
    for col in ['close', 'Close']:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        ax.text(0.5, 0.5, '가격 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # MACD 칼럼 이름 정의
    macd_col = f'macd_{fast_period}_{slow_period}_{signal_period}'
    signal_col = f'macd_signal_{fast_period}_{slow_period}_{signal_period}'
    hist_col = f'macd_hist_{fast_period}_{slow_period}_{signal_period}'
    
    # MACD 계산 (직관적인 컬럼명 확인을 위해 수정)
    macd_names = [
        # 표준 MACD 컬럼명
        (f'macd_{fast_period}_{slow_period}_{signal_period}', f'macd_signal_{fast_period}_{slow_period}_{signal_period}', f'macd_hist_{fast_period}_{slow_period}_{signal_period}'),
        # 다른 가능한 형식 추가
        ('macd', 'macd_signal', 'macd_hist'),
        ('MACD', 'MACD_Signal', 'MACD_Hist')
    ]
    
    # 모든 가능한 MACD 컬럼명 확인
    has_macd_data = False
    for macd_name, signal_name, hist_name in macd_names:
        if macd_name in df.columns and signal_name in df.columns:
            macd_col = macd_name
            signal_col = signal_name
            hist_col = hist_name if hist_name in df.columns else None
            has_macd_data = True
            break
    
    # 컬럼이 없으면 계산
    if not has_macd_data:
        try:
            print(f"MACD 계산 시작 (fast={fast_period}, slow={slow_period}, signal={signal_period})")
            
            # EMA 계산
            fast_ema = df[price_col].ewm(span=fast_period, adjust=False).mean()
            slow_ema = df[price_col].ewm(span=slow_period, adjust=False).mean()
            
            # MACD 라인
            df[macd_col] = fast_ema - slow_ema
            
            # 시그널 라인
            df[signal_col] = df[macd_col].ewm(span=signal_period, adjust=False).mean()
            
            # MACD 히스토그램 (MACD - 시그널)
            df[hist_col] = df[macd_col] - df[signal_col]
            
            print(f"MACD 계산 완료: {macd_col}, {signal_col}, {hist_col}")
            
            # 계산된 값 확인
            if df[macd_col].notna().sum() > 0 and df[signal_col].notna().sum() > 0:
                has_macd_data = True
                print(f"MACD 계산 값: min={df[macd_col].min():.2f}, max={df[macd_col].max():.2f}")
                print(f"MACD 신호선 값: min={df[signal_col].min():.2f}, max={df[signal_col].max():.2f}")
            else:
                print("MACD 계산 결과가 유효하지 않습니다.")
        except Exception as e:
            print(f"MACD 계산 중 오류 발생: {e}")
    
    if not has_macd_data or df[macd_col].empty or df[signal_col].empty:
        ax.text(0.5, 0.5, 'MACD 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # MACD 라인
    ax.plot(
        df.index, 
        df[macd_col], 
        color=style_config['colors'].get('macd', '#2196F3'), 
        linewidth=1.5, 
        label=f'MACD ({fast_period},{slow_period},{signal_period})'
    )
    
    # 시그널 라인
    ax.plot(
        df.index, 
        df[signal_col], 
        color=style_config['colors'].get('signal', '#FF9800'), 
        linewidth=1.5, 
        linestyle='--', 
        label='Signal'
    )
    
    # 히스토그램 계산 및 표시
    if hist_col and hist_col in df.columns:
        # 히스토그램 색상 설정 (양수/음수에 따라)
        colors = np.where(
            df[hist_col] >= 0, 
            style_config['colors'].get('macd_hist_positive', '#26A69A'), 
            style_config['colors'].get('macd_hist_negative', '#EF5350')
        )
        
        # 히스토그램 그리기
        for i in range(len(df)):
            if i < len(df) and not pd.isna(df[hist_col].iloc[i]):
                ax.bar(
                    df.index[i], 
                    df[hist_col].iloc[i], 
                    color=colors[i], 
                    alpha=0.7, 
                    width=0.8
                )
    
    # 0 라인
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
    
    # 축 설정
    ax.set_ylabel('MACD', fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid']['alpha'])
    
    # 범례 표시
    if show_legend:
        ax.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])

def plot_rsi(
    ax: plt.Axes, 
    df: pd.DataFrame, 
    style_config: Dict[str, Any],
    period: int = 14,
    overbought: int = 70,
    oversold: int = 30,
    show_legend: bool = True
) -> None:
    """
    RSI 차트 그리기
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
        period (int): RSI 기간
        overbought (int): 과매수 기준선
        oversold (int): 과매도 기준선
        show_legend (bool): 범례 표시 여부
        
    Returns:
        None
    """
    # 데이터프레임이 비어있는지 확인
    if df is None or df.empty:
        ax.text(0.5, 0.5, 'RSI 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 가격 컬럼 찾기 (대소문자 처리)
    price_col = None
    for col in ['close', 'Close']:
        if col in df.columns:
            price_col = col
            break
    
    if price_col is None:
        ax.text(0.5, 0.5, '가격 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # RSI 칼럼명 확인 (여러 가능한 형식)
    rsi_names = [f'rsi{period}', f'RSI{period}', 'rsi', 'RSI']
    rsi_col = None
    
    # 모든 가능한 RSI 컬럼명 확인
    for name in rsi_names:
        if name in df.columns:
            rsi_col = name
            break
    
    # RSI 컬럼이 없으면 계산
    if rsi_col is None:
        try:
            print(f"RSI 계산 시작 (period={period})")
            rsi_col = f'rsi{period}'  # 표준 이름 사용
            
            # 데이터 유효성 검사
            if len(df[price_col]) <= period:
                print(f"경고: RSI 계산에 필요한 데이터가 부족합니다. 최소 {period+1}개 필요, 현재 {len(df[price_col])}개")
                ax.text(0.5, 0.5, 'RSI 계산에 필요한 데이터 부족', ha='center', va='center', transform=ax.transAxes)
                return
                
            # 가격 변화
            delta = df[price_col].diff()
            
            # 상승/하락 분리
            gain = delta.copy()
            loss = delta.copy()
            gain[gain < 0] = 0
            loss[loss > 0] = 0
            loss = abs(loss)
            
            # 평균 상승/하락 계산 - 수정된 방식
            # 단순 이동평균으로 첫 기간을 계산
            avg_gain = gain.rolling(window=period, min_periods=1).mean()
            avg_loss = loss.rolling(window=period, min_periods=1).mean()
            
            # NaN 값을 0으로 대체하여 계산 안정화
            avg_gain.fillna(0, inplace=True)
            avg_loss.fillna(0, inplace=True)
            
            # 첫 번째 값 이후에는 지수 이동평균(EMA) 방식으로 계산
            for i in range(period+1, len(df)):
                if i >= len(avg_gain) or i >= len(avg_loss):
                    continue
                avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period-1) + gain.iloc[i]) / period
                avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period-1) + loss.iloc[i]) / period
            
            # RS와 RSI 계산 - 0으로 나누는 오류 방지
            rs = avg_gain / np.maximum(avg_loss, 1e-10)  # 분모가 0이면 작은 값으로 대체
            df[rsi_col] = 100 - (100 / (1 + rs))
            
            # 계산된 값 검증
            if np.isnan(df[rsi_col]).all():
                print("경고: RSI 계산 결과가 모두 NaN입니다. 계산 로직을 확인하세요.")
                ax.text(0.5, 0.5, 'RSI 계산 실패', ha='center', va='center', transform=ax.transAxes)
                return
                
            print(f"RSI 계산 완료: {rsi_col}")
            
            # 계산된 값 확인
            if df[rsi_col].notna().sum() > 0:
                print(f"RSI 계산 값: min={df[rsi_col].min():.2f}, max={df[rsi_col].max():.2f}")
            else:
                print("RSI 계산 결과가 유효하지 않습니다.")
        except Exception as e:
            print(f"RSI 계산 중 오류 발생: {e}")
            ax.text(0.5, 0.5, f'RSI 계산 오류: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            return
    
    # RSI 데이터가 있는지 확인
    if rsi_col is None or rsi_col not in df.columns or df[rsi_col].empty:
        ax.text(0.5, 0.5, 'RSI 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
        
    # RSI 데이터의 유효성 검사
    if df[rsi_col].isna().all():
        ax.text(0.5, 0.5, 'RSI 데이터가 모두 NaN', ha='center', va='center', transform=ax.transAxes)
        return
    
    # RSI 라인 - NaN 값은 건너뛰고 그리기
    valid_rsi = df[rsi_col].dropna()
    ax.plot(
        valid_rsi.index, 
        valid_rsi, 
        color=style_config['colors']['rsi'], 
        linewidth=1.5, 
        label=f'RSI ({period})'
    )
    
    # 과매수/과매도 영역 표시
    ax.axhline(y=overbought, color='red', linestyle='--', alpha=0.5)
    ax.axhline(y=oversold, color='green', linestyle='--', alpha=0.5)
    
    # 영역 칠하기
    ax.fill_between(df.index, overbought, 100, color='red', alpha=0.1)
    ax.fill_between(df.index, 0, oversold, color='green', alpha=0.1)
    
    # 축 설정
    ax.set_ylim(0, 100)
    ax.set_ylabel('RSI', fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid']['alpha'])
    
    # 범례 표시
    if show_legend:
        ax.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])

def plot_stochastic(
    ax: plt.Axes, 
    df: pd.DataFrame, 
    style_config: Dict[str, Any],
    k_period: int = 14,
    d_period: int = 3,
    overbought: int = 80,
    oversold: int = 20,
    show_legend: bool = True
) -> None:
    """
    스토캐스틱 차트 그리기
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
        k_period (int): %K 기간
        d_period (int): %D 기간
        overbought (int): 과매수 기준선
        oversold (int): 과매도 기준선
        show_legend (bool): 범례 표시 여부
        
    Returns:
        None
    """
    # 스토캐스틱 칼럼 이름
    k_col = f'stoch_k{k_period}'
    d_col = f'stoch_d{k_period}_{d_period}'
    
    # 스토캐스틱 칼럼 확인 및 계산
    has_stoch_data = True
    
    if k_col not in df.columns or d_col not in df.columns:
        has_stoch_data = False
        
        try:
            # %K: (현재 종가 - n일간 최저가) / (n일간 최고가 - n일간 최저가) * 100
            low_min = df['low'].rolling(window=k_period).min()
            high_max = df['high'].rolling(window=k_period).max()
            
            df[k_col] = 100 * ((df['close'] - low_min) / (high_max - low_min))
            
            # %D: %K의 m일 이동평균
            df[d_col] = df[k_col].rolling(window=d_period).mean()
            
            has_stoch_data = True
        except Exception as e:
            print(f"스토캐스틱 계산 중 오류 발생: {e}")
    
    if not has_stoch_data:
        ax.text(0.5, 0.5, '스토캐스틱 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # %K 라인
    ax.plot(
        df.index, 
        df[k_col], 
        color=style_config['colors']['stoch'], 
        linewidth=1.5, 
        label=f'%K ({k_period})'
    )
    
    # %D 라인
    ax.plot(
        df.index, 
        df[d_col], 
        color=style_config['colors']['stoch_signal'], 
        linewidth=1.5, 
        linestyle='--', 
        label=f'%D ({d_period})'
    )
    
    # 과매수/과매도 영역
    # 과매수 영역
    ax.fill_between(
        df.index, 
        overbought, 
        100, 
        color=style_config['colors']['sell_signal'], 
        alpha=0.2
    )
    
    # 과매도 영역
    ax.fill_between(
        df.index, 
        0, 
        oversold, 
        color=style_config['colors']['buy_signal'], 
        alpha=0.2
    )
    
    # 기준선
    ax.axhline(y=overbought, color=style_config['colors']['sell_signal'], linestyle='--', alpha=0.7)
    ax.axhline(y=oversold, color=style_config['colors']['buy_signal'], linestyle='--', alpha=0.7)
    ax.axhline(y=50, color='black', linestyle='-', alpha=0.3)
    
    # 레이블 추가
    ax.text(
        df.index[0], 
        overbought + 2, 
        f'과매수 ({overbought})', 
        color=style_config['colors']['text'], 
        fontsize=style_config['fontsize']['annotation'],
        alpha=0.8
    )
    
    ax.text(
        df.index[0], 
        oversold - 2, 
        f'과매도 ({oversold})', 
        color=style_config['colors']['text'], 
        fontsize=style_config['fontsize']['annotation'], 
        alpha=0.8
    )
    
    # Y축 범위 설정
    ax.set_ylim(0, 100)
    
    # 축 설정
    ax.set_ylabel('스토캐스틱', fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid']['alpha'])
    
    # 범례 표시
    if show_legend:
        ax.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])

def plot_atr(
    ax: plt.Axes, 
    df: pd.DataFrame, 
    style_config: Dict[str, Any],
    period: int = 14,
    show_percentage: bool = True,
    show_legend: bool = True
) -> None:
    """
    ATR(Average True Range) 차트 그리기
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
        period (int): ATR 기간
        show_percentage (bool): ATR 백분율로 표시 여부
        show_legend (bool): 범례 표시 여부
        
    Returns:
        None
    """
    # ATR 칼럼 이름
    atr_col = f'atr{period}'
    atr_pct_col = f'atr{period}_pct'
    
    # ATR 칼럼 확인 및 계산
    if atr_col not in df.columns:
        try:
            # True Range 계산
            high_low = df['high'] - df['low']
            high_close_prev = abs(df['high'] - df['close'].shift(1))
            low_close_prev = abs(df['low'] - df['close'].shift(1))
            
            tr = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
            
            # ATR 계산 (단순 이동평균)
            df[atr_col] = tr.rolling(window=period).mean()
            
            # ATR 백분율 계산
            df[atr_pct_col] = (df[atr_col] / df['close']) * 100
        except Exception as e:
            print(f"ATR 계산 중 오류 발생: {e}")
    
    # ATR 데이터가 있는지 확인
    if atr_col not in df.columns:
        ax.text(0.5, 0.5, 'ATR 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 사용할 데이터 선택 (원시 ATR 또는 백분율)
    plot_col = atr_pct_col if show_percentage and atr_pct_col in df.columns else atr_col
    y_label = 'ATR %' if show_percentage and atr_pct_col in df.columns else 'ATR'
    
    # ATR 라인
    ax.plot(
        df.index, 
        df[plot_col], 
        color=style_config['colors']['macd'], 
        linewidth=1.5, 
        label=f'ATR ({period})'
    )
    
    # 평균선 (기준점) - 전체 기간의 평균 ATR
    avg_value = df[plot_col].mean()
    ax.axhline(y=avg_value, color='black', linestyle='--', alpha=0.5, label='평균')
    
    # 평균 텍스트 표시
    ax_ymin, ax_ymax = ax.get_ylim()
    avg_text = f'평균: {avg_value:.2f}%' if show_percentage else f'평균: {avg_value:.2f}'
    
    ax.text(
        df.index[-1], 
        avg_value, 
        avg_text, 
        color=style_config['colors']['text'], 
        fontsize=style_config['fontsize']['annotation'],
        alpha=0.8,
        ha='right',
        va='bottom'
    )
    
    # 축 설정
    ax.set_ylabel(y_label, fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid']['alpha'])
    
    # Y축 서식 지정
    if show_percentage:
        ax.yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(decimals=1))
    
    # 범례 표시
    if show_legend:
        ax.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])

def plot_cci(
    ax: plt.Axes, 
    df: pd.DataFrame, 
    style_config: Dict[str, Any],
    period: int = 20,
    constant: float = 0.015,
    overbought: int = 100,
    oversold: int = -100,
    show_legend: bool = True
) -> None:
    """
    CCI(Commodity Channel Index) 차트 그리기
    
    Parameters:
        ax (plt.Axes): 축 객체
        df (pd.DataFrame): 데이터프레임
        style_config (Dict[str, Any]): 스타일 설정
        period (int): CCI 기간
        constant (float): CCI 계산에 사용되는 상수
        overbought (int): 과매수 기준선
        oversold (int): 과매도 기준선
        show_legend (bool): 범례 표시 여부
        
    Returns:
        None
    """
    # CCI 칼럼 이름
    cci_col = f'cci{period}'
    
    # CCI 칼럼 확인 및 계산
    if cci_col not in df.columns:
        try:
            # 전형적 가격 (TP) = (고가 + 저가 + 종가) / 3
            tp = (df['high'] + df['low'] + df['close']) / 3
            
            # TP의 n일 단순 이동평균
            tp_sma = tp.rolling(window=period).mean()
            
            # TP의 평균 편차
            tp_mad = tp.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
            
            # CCI 계산: (TP - TP의 n일 SMA) / (일정 상수 * TP의 평균 편차)
            df[cci_col] = (tp - tp_sma) / (constant * tp_mad)
        except Exception as e:
            print(f"CCI 계산 중 오류 발생: {e}")
    
    # CCI 데이터가 있는지 확인
    if cci_col not in df.columns:
        ax.text(0.5, 0.5, 'CCI 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # CCI 라인
    ax.plot(
        df.index, 
        df[cci_col], 
        color=style_config['colors']['rsi'], 
        linewidth=1.5, 
        label=f'CCI ({period})'
    )
    
    # 과매수/과매도 영역
    # 과매수 영역
    ax.fill_between(
        df.index, 
        overbought, 
        ax.get_ylim()[1], 
        color=style_config['colors']['sell_signal'], 
        alpha=0.2
    )
    
    # 과매도 영역
    ax.fill_between(
        df.index, 
        ax.get_ylim()[0], 
        oversold, 
        color=style_config['colors']['buy_signal'], 
        alpha=0.2
    )
    
    # 기준선
    ax.axhline(y=overbought, color=style_config['colors']['sell_signal'], linestyle='--', alpha=0.7)
    ax.axhline(y=oversold, color=style_config['colors']['buy_signal'], linestyle='--', alpha=0.7)
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # 레이블 추가
    ax.text(
        df.index[0], 
        overbought + 20, 
        f'과매수 ({overbought})', 
        color=style_config['colors']['text'], 
        fontsize=style_config['fontsize']['annotation'],
        alpha=0.8
    )
    
    ax.text(
        df.index[0], 
        oversold - 20, 
        f'과매도 ({oversold})', 
        color=style_config['colors']['text'], 
        fontsize=style_config['fontsize']['annotation'], 
        alpha=0.8
    )
    
    # 축 설정
    ax.set_ylabel('CCI', fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid']['alpha'])
    
    # 범례 표시
    if show_legend:
        ax.legend(loc='upper left', fontsize=style_config['fontsize']['legend'])

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
    # 데이터프레임이 비어있는지 확인
    if df is None or df.empty:
        ax.text(0.5, 0.5, '거래량 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 거래량 컬럼 확인 (대소문자 처리)
    volume_col = None
    for col in ['volume', 'Volume']:
        if col in df.columns:
            volume_col = col
            break
    
    # 변동성 컬럼이 없는 경우 메시지 표시
    if volume_col is None:
        ax.text(0.5, 0.5, '거래량 데이터 없음', ha='center', va='center', transform=ax.transAxes)
        return
    
    # 상승/하락에 따른 색상 설정
    close_col = 'close' if 'close' in df.columns else 'Close'
    open_col = 'open' if 'open' in df.columns else 'Open'
    
    # 색상 설정 (종가가 시가보다 높으면 매수색, 낮으면 매도색)
    colors = np.where(
        df[close_col] >= df[close_col].shift(1),
        style_config['colors'].get('up', '#26a69a'),
        style_config['colors'].get('down', '#ef5350')
    )
    
    # 거래량 그리기
    ax.bar(df.index, df[volume_col], color=colors, alpha=0.7, width=0.8)
    
    # 축 설정
    ax.set_ylabel('거래량', fontsize=style_config['fontsize']['label'])
    ax.grid(True, alpha=style_config['grid'].get('alpha', 0.15))
    
    # Y축에 천 단위 구분기호 추가
    ax.yaxis.set_major_formatter(plt.matplotlib.ticker.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))

def plot_indicator_chart(
    df: pd.DataFrame,
    ticker: str,
    indicators: List[str] = ['rsi', 'macd'],
    chart_dir: Optional[str] = None,
    style: str = 'default',
    interval: str = '1d',
    period: str = '3m',
    save: bool = True,
    indicator_params: Optional[Dict[str, Dict[str, Any]]] = None
) -> Tuple[Figure, List, str]:
    """
    여러 기술 지표를 표시하는 차트 생성
    
    Parameters:
        df (pd.DataFrame): OHLCV 데이터프레임
        ticker (str): 티커 심볼
        indicators (List[str]): 표시할 지표 목록 ('rsi', 'macd', 'stoch', 'atr', 'cci')
        chart_dir (str, optional): 차트 저장 디렉토리
        style (str): 차트 스타일
        interval (str): 데이터 간격
        period (str): 기간
        save (bool): 차트 저장 여부
        indicator_params (Dict[str, Dict[str, Any]], optional): 지표별 파라미터
        
    Returns:
        Tuple[Figure, List, str]: (fig, axes, 저장된 차트 경로)
    """
    # 차트 디렉토리 설정
    if chart_dir is None:
        chart_dir = setup_chart_dir(CHART_SAVE_PATH)
    
    # 스타일 설정
    style_config = apply_style(style)
    
    # 데이터 준비
    df = prepare_ohlcv_dataframe(df)
    
    # 유효한 지표 확인
    valid_indicators = ['rsi', 'macd', 'stoch', 'atr', 'cci']
    indicators = [ind.lower() for ind in indicators if ind.lower() in valid_indicators]
    
    if not indicators:
        print("유효한 지표가 지정되지 않았습니다. 기본값으로 RSI와 MACD를 사용합니다.")
        indicators = ['rsi', 'macd']
    
    # 지표별 매개변수 기본값 설정
    default_params = {
        'rsi': {'period': 14, 'overbought': 70, 'oversold': 30},
        'macd': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
        'stoch': {'k_period': 14, 'd_period': 3, 'overbought': 80, 'oversold': 20},
        'atr': {'period': 14, 'show_percentage': True},
        'cci': {'period': 20, 'constant': 0.015, 'overbought': 100, 'oversold': -100}
    }
    
    # 사용자 지정 매개변수로 업데이트
    if indicator_params:
        for ind, params in indicator_params.items():
            if ind.lower() in default_params:
                default_params[ind.lower()].update(params)
    
    # 그리드 설정
    fig = plt.figure(figsize=(12, 4 * len(indicators)), dpi=style_config['figure']['dpi'])
    gs = gridspec.GridSpec(len(indicators), 1, height_ratios=[1] * len(indicators))
    
    # 차트 제목 설정
    indicator_names = {
        'rsi': 'RSI',
        'macd': 'MACD',
        'stoch': '스토캐스틱',
        'atr': 'ATR',
        'cci': 'CCI'
    }
    
    title_parts = [indicator_names.get(ind, ind.upper()) for ind in indicators]
    title = f"{ticker} 기술 지표: {', '.join(title_parts)} ({period}, {interval})"
    
    plt.suptitle(title, fontsize=style_config['fontsize']['title'])
    
    # 각 지표별 차트 생성
    axes = []
    
    for i, indicator in enumerate(indicators):
        ax = fig.add_subplot(gs[i])
        axes.append(ax)
        
        # 지표별 매개변수
        params = default_params[indicator]
        
        # 지표 그리기
        if indicator == 'rsi':
            plot_rsi(ax, df, style_config, **params)
        elif indicator == 'macd':
            plot_macd(ax, df, style_config, **params)
        elif indicator == 'stoch':
            plot_stochastic(ax, df, style_config, **params)
        elif indicator == 'atr':
            plot_atr(ax, df, style_config, **params)
        elif indicator == 'cci':
            plot_cci(ax, df, style_config, **params)
        
        # X축 날짜 포맷 설정
        format_date_axis(ax)
    
    # 레이아웃 조정
    plt.tight_layout()
    plt.subplots_adjust(top=0.95)
    
    # 차트 저장
    chart_path = ''
    if save:
        indicator_prefix = '_'.join([ind[:3] for ind in indicators])
        filename = f"{ticker}_{indicator_prefix}_{interval}_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        chart_path = os.path.join(chart_dir, filename)
        plt.savefig(chart_path, dpi=style_config['figure']['dpi'], bbox_inches='tight')
    
    return fig, axes, chart_path 