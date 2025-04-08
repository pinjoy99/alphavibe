import pyupbit
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
# 한글 폰트 설정 전에 unicode minus 설정
matplotlib.rcParams['axes.unicode_minus'] = False
from datetime import datetime, timedelta
import os
import sys
import argparse
from dotenv import load_dotenv
from telegram import Bot
import asyncio
from typing import Optional, Dict, Any, List
import numpy as np
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import koreanize_matplotlib  # 한글 폰트 적용
# 한글 폰트 적용 후 다시 설정 (koreanize가 재설정할 수 있음)
matplotlib.rcParams['axes.unicode_minus'] = False
from src.api.upbit_api import get_historical_data, parse_period_to_datetime, get_backtest_data
from src.backtest import run_backtest_bt  # Backtesting.py 백테스팅 함수만 import
from src.strategies.strategy_registry import StrategyRegistry
from src.strategies.sma_strategy_bt import SMAStrategyBT  # Backtesting.py 기반 SMA 전략
from src.notification import (
    send_telegram_message,
    send_telegram_chart,
    get_telegram_backtest_message,
    get_telegram_analysis_message
)

# 시각화 모듈 추가
from src.visualization import (
    plot_price_with_indicators,
    setup_chart_dir
)

# 계좌 조회 기능 추가
from src.trading.account import AccountManager
from src.visualization.trading_charts import plot_asset_distribution, plot_profit_loss

# 설정 모듈 추가
from src.utils.config import DEFAULT_COINS, DEFAULT_INTERVAL, DEFAULT_BACKTEST_PERIOD, DEFAULT_INITIAL_CAPITAL

# 명령줄 인자 파싱
def parse_args():
    parser = argparse.ArgumentParser(description="암호화폐 가격 분석")
    parser.add_argument("--telegram", "-t", action="store_true", help="텔레그램 알림 활성화")
    parser.add_argument("--backtest", "-b", action="store_true", help="백테스팅 모드 활성화")
    
    # 사용 가능한 전략 목록 동적 생성
    StrategyRegistry.discover_strategies()
    available_strategies = [strategy['code'] for strategy in StrategyRegistry.get_available_strategies()]
    available_strategies = sorted(list(set(available_strategies)))  # 중복 제거 및 정렬
    
    parser.add_argument("--strategy", "-s", choices=available_strategies, default="sma", 
                      help="백테스팅 전략 선택 (기본값: sma)")
    parser.add_argument("--period", "-p", type=str, default=DEFAULT_BACKTEST_PERIOD, 
                      help="백테스팅 기간 또는 분석 기간 (예: 1d, 3d, 1w, 1m, 3m, 6m, 1y)")
    parser.add_argument("--invest", "-i", type=float, default=DEFAULT_INITIAL_CAPITAL, 
                      help=f"백테스팅 초기 투자금액 (원화, 기본값: {DEFAULT_INITIAL_CAPITAL:,}원)")
    parser.add_argument("--account", "-a", action="store_true", help="계좌 정보 조회")
    parser.add_argument("--coins", "-c", type=str, default=DEFAULT_COINS, 
                      help=f"분석할 코인 목록 (쉼표로 구분, 기본값: {DEFAULT_COINS})")
    parser.add_argument("--interval", "-v", type=str, default=DEFAULT_INTERVAL, 
                      help=f"데이터 간격 (예: day, minute15, minute60, 기본값: {DEFAULT_INTERVAL})")
    parser.add_argument("--params", type=str, 
                      help="전략 파라미터 (쉼표로 구분된 key=value 쌍, 예: short_window=10,long_window=30)")
    parser.add_argument("--style", type=str, choices=["default", "dark", "tradingview"], default="default",
                      help="차트 스타일 (기본값: default)")
    return parser.parse_args()

# Load environment variables
load_dotenv()

# Get settings from environment variables
CHART_SAVE_PATH = os.getenv('CHART_SAVE_PATH', 'results/analysis')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# API key settings
UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------
# 백테스팅 실행 함수
# ----------------------

async def run_backtest(bot: Optional[Bot], ticker: str, strategy: str, period: str, initial_capital: float, enable_telegram: bool, interval: str = "minute60", params: Dict[str, Any] = None) -> None:
    """
    백테스팅 실행
    
    Parameters:
        bot (Optional[Bot]): 텔레그램 봇 인스턴스
        ticker (str): 종목 심볼
        strategy (str): 전략 이름
        period (str): 백테스팅 기간
        initial_capital (float): 초기 투자금액
        enable_telegram (bool): 텔레그램 알림 활성화 여부
        interval (str): 데이터 간격 (기본값: minute60)
        params (Dict[str, Any]): 전략 파라미터
    """
    print(f"\n백테스팅 시작: {ticker} (전략: {strategy}, 기간: {period}, 간격: {interval})")
    
    if enable_telegram:
        await send_telegram_message(f"🔍 백테스팅 시작: {ticker} (전략: {strategy}, 기간: {period}, 간격: {interval})", enable_telegram, bot)
    
    # 백테스팅 데이터 조회
    df = get_backtest_data(ticker, period, interval)
    
    if df is not None and not df.empty:
        # 레지스트리에서 전략 정보 가져오기
        strategy_info = None
        for s in StrategyRegistry.get_available_strategies():
            if s['code'] == strategy:
                strategy_info = s
                break
        
        # 전략 파라미터 설정 - 레지스트리 정보 사용
        strategy_params = {}
        if strategy_info:
            strategy_params = {p['name']: p['default'] for p in strategy_info['params']}
            
        # 사용자 지정 파라미터로 업데이트
        if params:
            strategy_params.update(params)
        
        try:
            results = None
            
            # 현재는 SMA 전략만 구현되어 있으므로 SMA 전략만 처리
            if strategy == 'sma':
                # 전략 파라미터 적용
                short_window = strategy_params.get('short_window', 10)
                long_window = strategy_params.get('long_window', 30)
                
                print(f"Backtesting.py 사용 - SMA 파라미터: short_window={short_window}, long_window={long_window}")
                
                results = run_backtest_bt(
                    df=df,
                    strategy_class=SMAStrategyBT,
                    initial_capital=initial_capital,
                    strategy_name="SMA Strategy",
                    ticker=ticker,
                    short_window=short_window,
                    long_window=long_window
                )
            else:
                error_message = f"현재 {strategy} 전략은 지원되지 않습니다. SMA 전략만 사용 가능합니다."
                print(f"\n⚠️ {error_message}")
                if enable_telegram:
                    await send_telegram_message(f"⚠️ {error_message}", enable_telegram, bot)
                return
            
            if results:
                # 결과 출력
                print("\n백테스팅 결과:")
                print(f"기간: {results['start_date']} ~ {results['end_date']} ({results['total_days']}일)")
                print(f"초기 자본금: {results['initial_capital']:,.0f} KRW")
                print(f"최종 자본금: {results.get('final_asset', 0):,.0f} KRW")
                print(f"총 수익률: {results.get('return_pct', 0):.2f}%")
                print(f"최대 낙폭: {results.get('max_drawdown', 0):.2f}%")
                print(f"거래 횟수: {results.get('total_trades', 0)}")
                
                if 'win_rate' in results:
                    print(f"승률: {results['win_rate']:.2f}%")
                if 'sharpe_ratio' in results:
                    print(f"샤프 비율: {results['sharpe_ratio']:.2f}")
                
                # 텔레그램 알림
                if enable_telegram:
                    # 결과 메시지 작성
                    params_str = ", ".join([f"{k}={v}" for k, v in strategy_params.items()])
                    
                    # 메시지 생성과 전송을 분리된 모듈 함수 사용
                    result_message = get_telegram_backtest_message(ticker, strategy, params_str, results)
                    
                    # 차트 전송
                    await send_telegram_chart(results.get('chart_path'), result_message, enable_telegram, bot)
                    
        except Exception as e:
            error_message = f"백테스팅 중 오류 발생: {e}"
            print(f"\n❌ {error_message}")
            if enable_telegram:
                await send_telegram_message(f"❌ {error_message}", enable_telegram, bot)
    else:
        error_message = f"백테스팅 데이터 조회 실패: {ticker}"
        print(error_message)
        if enable_telegram:
            await send_telegram_message(f"❌ {error_message}", enable_telegram, bot)

async def analyze_ticker(bot: Optional[Bot], ticker: str, enable_telegram: bool, interval: str = "day", period: str = "3m") -> None:
    """
    단일 코인 분석 수행
    
    Parameters:
        bot (Optional[Bot]): 텔레그램 봇 인스턴스
        ticker (str): 종목 심볼
        enable_telegram (bool): 텔레그램 알림 활성화 여부
        interval (str): 데이터 간격 (기본값: day)
        period (str): 분석 기간 (기본값: 3m)
    """
    print(f"\n{ticker} 분석 중... (간격: {interval}, 기간: {period})")
    
    if enable_telegram:
        await send_telegram_message(f"🔍 {ticker} 분석 시작... (간격: {interval}, 기간: {period})", enable_telegram, bot)
    
    # 새로운 분석 모듈 사용
    try:
        from src.analysis import analyze_market
        
        # 분석 수행
        analysis_result = analyze_market(ticker, period, interval)
        
        if 'error' in analysis_result:
            error_message = f"{ticker} 분석 실패: {analysis_result['error']}"
            print(error_message)
            if enable_telegram:
                await send_telegram_message(f"❌ {error_message}", enable_telegram, bot)
            return
            
        # 분석 결과 출력
        stats = analysis_result['stats']
        print("\n기본 통계:")
        print(f"시작일: {stats['start_date']}")
        print(f"종료일: {stats['end_date']}")
        print(f"최고가: {stats['highest_price']:,.0f} KRW")
        print(f"최저가: {stats['lowest_price']:,.0f} KRW")
        print(f"총 거래량: {stats['volume']:,.0f}")
        
        # 기술적 지표 정보 출력
        print("\n기술적 지표 분석:")
        for indicator, value in analysis_result['technical_indicators'].items():
            print(f"{indicator}: {value}")
        
        # 지지선/저항선 정보 출력
        if 'support_levels' in analysis_result and analysis_result['support_levels']:
            print("\n주요 지지선:")
            for level in analysis_result['support_levels']:
                print(f"  - {level:,.0f} KRW")
        
        if 'resistance_levels' in analysis_result and analysis_result['resistance_levels']:
            print("\n주요 저항선:")
            for level in analysis_result['resistance_levels']:
                print(f"  - {level:,.0f} KRW")
                
        # 차트 경로 가져오기
        chart_path = analysis_result.get('chart_path', '')
        
        # 텔레그램 알림
        if enable_telegram and chart_path:
            # 기술적 지표 요약 메시지 생성
            technical_message = f"📊 *{ticker} 기술적 분석*\n\n"
            technical_message += f"현재가: `{stats['current_price']:,.0f} KRW` "
            
            # 가격 변화 정보 추가
            pct_change = stats['price_pct_change']
            price_change = stats['price_change']
            change_sign = "+" if price_change > 0 else ""
            technical_message += f"({change_sign}{pct_change:.2f}%)\n\n"
            
            # 지지/저항선 추가
            if analysis_result['support_levels']:
                support_text = ', '.join([f"{level:,.0f}" for level in analysis_result['support_levels']])
                technical_message += f"🔻 *지지선*: `{support_text} KRW`\n"
            
            if analysis_result['resistance_levels']:
                resistance_text = ', '.join([f"{level:,.0f}" for level in analysis_result['resistance_levels']])
                technical_message += f"🔺 *저항선*: `{resistance_text} KRW`\n\n"
            
            # 기술적 지표 요약 추가
            technical_message += "*기술적 지표 요약:*\n"
            for indicator, value in analysis_result['technical_indicators'].items():
                technical_message += f"• *{indicator}*: {value}\n"
            
            # 차트와 함께 메시지 전송
            await send_telegram_chart(chart_path, technical_message, enable_telegram, bot)
        else:
            if not chart_path:
                print("\n⚠️ 경고: 차트 생성 실패")
                
    except Exception as e:
        error_message = f"{ticker} 분석 중 오류 발생: {e}"
        print(error_message)
        import traceback
        traceback.print_exc()
        if enable_telegram:
            await send_telegram_message(f"❌ {error_message}", enable_telegram, bot)

async def check_account(bot: Optional[Bot], enable_telegram: bool) -> None:
    """
    계좌 정보 조회 및 분석
    
    Parameters:
        bot (Optional[Bot]): 텔레그램 봇 인스턴스
        enable_telegram (bool): 텔레그램 알림 활성화 여부
    """
    print("\n계좌 정보 조회를 시작합니다...")
    
    if enable_telegram:
        await send_telegram_message("🔍 계좌 정보 조회를 시작합니다...", enable_telegram, bot)
    
    # 계좌 정보 조회
    account_manager = AccountManager()
    if not account_manager.refresh():
        error_message = "❌ 계좌 정보 조회 실패: API 키를 확인하세요."
        print(error_message)
        if enable_telegram:
            await send_telegram_message(error_message, enable_telegram, bot)
        return
    
    # 계좌 요약 정보 (500원 이상 코인만 표시, 가치 기준 정렬)
    summary = account_manager.get_summary(min_value=500.0, sort_by='value')
    
    # 콘솔에 출력
    print("\n===== 계좌 정보 요약 =====")
    print(f"조회 시간: {summary.get('last_update', '정보 없음')}")
    print(f"보유 현금: {summary.get('total_krw', 0):,.0f} KRW")
    print(f"총 자산 가치: {summary.get('total_asset_value', 0):,.0f} KRW")
    
    # 손익 정보 (총 손익이 있는 경우만 표시)
    total_profit_loss = summary.get('total_profit_loss', 0)
    if total_profit_loss != 0:
        profit_sign = "+" if total_profit_loss > 0 else ""
        print(f"총 손익: {profit_sign}{total_profit_loss:,.0f} KRW ({profit_sign}{summary.get('total_profit_loss_pct', 0):.2f}%)")
    
    # 코인별 보유 현황 출력
    coins = summary.get('coins', [])
    if coins:
        print("\n----- 코인별 보유 현황 -----")
        for coin in coins:
            print(f"{coin['currency']} ({coin['ticker']}):")
            print(f"  보유량: {coin['balance']:.8f}")
            print(f"  매수 평균가: {coin['avg_buy_price']:,.0f} KRW")
            print(f"  현재가: {coin['current_price']:,.0f} KRW")
            print(f"  평가금액: {coin['current_value']:,.0f} KRW")
            
            # 손익 정보 (변화가 있는 경우만 표시)
            if coin['profit_loss'] != 0:
                profit_sign = "+" if coin['profit_loss'] > 0 else ""
                print(f"  손익: {profit_sign}{coin['profit_loss']:,.0f} KRW ({profit_sign}{coin['profit_loss_pct']:.2f}%)")
            print("----------------------------")
    
    # 소액 코인 정보 표시
    others = summary.get('others', {})
    if others.get('count', 0) > 0:
        print(f"\n----- 소액 코인 ({others.get('count', 0)}개) -----")
        print(f"총 평가금액: {others.get('total_value', 0):,.0f} KRW")
        if others.get('total_profit_loss', 0) != 0:
            profit_sign = "+" if others.get('total_profit_loss', 0) > 0 else ""
            print(f"총 손익: {profit_sign}{others.get('total_profit_loss', 0):,.0f} KRW")
        print("----------------------------")
    else:
        print("\n소액 코인이 없습니다.")
    
    # 최근 주문 내역
    orders = account_manager.get_recent_orders(limit=5)
    if orders and len(orders) > 0:
        print("\n----- 최근 5개 주문 내역 -----")
        for order in orders:
            print(f"{order['created_at']} | {order['ticker']} | {order['side']} | " +
                  f"가격: {order['price']:,.0f} KRW | 수량: {order['executed_volume']:.8f} | " +
                  f"금액: {order['amount']:,.0f} KRW")
    else:
        print("\n최근 주문 내역이 없습니다.")
    
    # 계좌 히스토리 저장
    try:
        history_path = account_manager.save_account_history()
        if history_path:
            print(f"\n계좌 히스토리 저장 완료: {history_path}")
    except Exception as e:
        print(f"\n계좌 히스토리 저장 실패: {e}")
    
    # 시각화
    try:
        chart_dir = setup_chart_dir('results/account')
        
        # 자산이 있는 경우만 차트 생성
        if summary['total_asset_value'] > 0:
            # 자산 분포 차트
            asset_chart_path = plot_asset_distribution(summary, chart_dir)
            print(f"자산 분포 차트 저장 완료: {asset_chart_path}")
            
            # 손익이 있는 코인이 있는 경우만 손익 차트 생성
            if any(coin['invested_value'] > 0 for coin in coins):
                profit_chart_path = plot_profit_loss(summary, chart_dir)
                print(f"손익 차트 저장 완료: {profit_chart_path}")
            
                # 텔레그램 전송
                if enable_telegram:
                    # 요약 메시지 생성
                    message = f"💰 *계좌 정보 요약*\n\n"
                    message += f"📊 총 자산 가치: `{summary.get('total_asset_value', 0):,.0f} KRW`\n"
                    message += f"💵 보유 현금: `{summary.get('total_krw', 0):,.0f} KRW`\n"
                    
                    if total_profit_loss != 0:
                        profit_sign = "+" if total_profit_loss > 0 else ""
                        message += f"📈 총 손익: `{profit_sign}{total_profit_loss:,.0f} KRW ({profit_sign}{summary.get('total_profit_loss_pct', 0):.2f}%)`\n\n"
                    
                    # 코인 정보 추가 (보유량이 있는 코인만)
                    active_coins = [c for c in coins if c['balance'] > 0]
                    if active_coins:
                        message += f"*코인별 보유 현황:*\n"
                        for coin in active_coins[:10]:  # 너무 길어지지 않도록 상위 10개만
                            profit_sign = "+" if coin['profit_loss_pct'] > 0 else ""
                            message += f"• *{coin['currency']}*: {coin['balance']:.8f} ({profit_sign}{coin['profit_loss_pct']:.2f}%)\n"
                        
                        # 나머지 코인 수 표시
                        if len(active_coins) > 10:
                            message += f"• 그 외 {len(active_coins) - 10}개 코인...\n"
                    
                    # 소액 코인 정보 추가
                    if others.get('count', 0) > 0:
                        message += f"\n*소액 코인:* {others.get('count', 0)}개 (총 `{others.get('total_value', 0):,.0f} KRW`)\n"
                    
                    # 차트 전송
                    await send_telegram_chart(asset_chart_path, message, enable_telegram, bot)
                    
                    # 손익 차트 전송
                    if 'profit_chart_path' in locals():
                        await send_telegram_chart(profit_chart_path, "💹 *코인별 손익 현황*", enable_telegram, bot)
        else:
            print("자산 분포/손익 차트 생성 건너뜀 (자산 없음)")
            
            if enable_telegram:
                message = f"💰 *계좌 정보 요약*\n\n"
                message += f"📊 총 자산 가치: `{summary.get('total_asset_value', 0):,.0f} KRW`\n"
                message += f"💵 보유 현금: `{summary.get('total_krw', 0):,.0f} KRW`\n"
                message += f"\n코인 보유 내역이 없습니다."
                await send_telegram_message(message, enable_telegram, bot)
    except Exception as e:
        error_message = f"차트 생성 실패: {e}"
        print(error_message)
        if enable_telegram:
            await send_telegram_message(f"❌ {error_message}", enable_telegram, bot)

# 메인 함수
async def main():
    # 명령줄 인자 파싱
    args = parse_args()
    
    # 설정값
    enable_telegram = args.telegram
    backtest_mode = args.backtest
    account_mode = args.account
    strategy = args.strategy
    period = args.period
    initial_capital = args.invest
    coin_list = args.coins.split(',')
    interval = args.interval
    
    # 전략 파라미터 파싱
    strategy_params = {}
    if args.params:
        for param in args.params.split(','):
            if '=' in param:
                key, value = param.split('=')
                # 숫자는 float로 변환 (정수로 표현 가능하면 int로)
                try:
                    num_value = float(value)
                    if num_value.is_integer():
                        num_value = int(num_value)
                    strategy_params[key] = num_value
                except ValueError:
                    # 숫자가 아니면 문자열로 유지
                    strategy_params[key] = value
    
    # 텔레그램 설정
    bot = None
    if enable_telegram:
        try:
            TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
            TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
            
            if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
                print("⚠️ 텔레그램 설정이 완료되지 않았습니다. .env 파일을 확인하세요.")
                enable_telegram = False
            else:
                bot = Bot(token=TELEGRAM_TOKEN)
        except Exception as e:
            print(f"⚠️ 텔레그램 설정 중 오류: {e}")
            enable_telegram = False
    
    # 차트 저장 디렉토리 설정
    setup_chart_dir()
    
    # 계좌 조회 모드
    if account_mode:
        await check_account(bot, enable_telegram)
        return
    
    # 백테스팅 모드
    if backtest_mode:
        for ticker in coin_list:
            # KRW- 접두사 추가 (없는 경우)
            if not ticker.startswith("KRW-"):
                ticker = f"KRW-{ticker}"
                
            # 백테스팅 실행
            await run_backtest(
                bot=bot, 
                ticker=ticker, 
                strategy=strategy, 
                period=period, 
                initial_capital=initial_capital, 
                enable_telegram=enable_telegram, 
                interval=interval,
                params=strategy_params  # 전략 파라미터 전달
            )
        return
        
    # 분석 모드 (기본)
    for ticker in coin_list:
        # KRW- 접두사 추가 (없는 경우)
        if not ticker.startswith("KRW-"):
            ticker = f"KRW-{ticker}"
        
        # 분석 실행
        await analyze_ticker(bot, ticker, enable_telegram, interval, period)

# 스크립트 실행
if __name__ == "__main__":
    asyncio.run(main()) 