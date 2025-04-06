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
from src.backtest import (
    backtest_strategy,
    plot_backtest_results
)
from src.strategies import create_strategy
from src.strategies.strategy_registry import StrategyRegistry
from src.notification import (
    send_telegram_message,
    send_telegram_chart,
    get_telegram_backtest_message,
    get_telegram_analysis_message
)

# 시각화 모듈 추가
from src.visualization import (
    plot_price_chart,
    setup_chart_dir
)

# 계좌 조회 기능 추가
from src.trading.account import AccountManager
from src.visualization.account_charts import plot_asset_distribution, plot_profit_loss

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
    return parser.parse_args()

# Load environment variables
load_dotenv()

# Get settings from environment variables
CHART_SAVE_PATH = os.getenv('CHART_SAVE_PATH', 'results/analysis')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# API key settings
UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')

# 백테스팅 설정
BACKTEST_RESULT_PATH = os.getenv('BACKTEST_RESULT_PATH', 'results/strategy_results')

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------
# 백테스팅 실행 함수
# ----------------------

async def run_backtest(bot: Optional[Bot], ticker: str, strategy: str, period: str, initial_capital: float, enable_telegram: bool, interval: str = "minute60") -> None:
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
        
        # 전략 객체 생성 및 적용
        strategy_obj = create_strategy(strategy, **strategy_params)
        if strategy_obj:
            try:
                # 전략 적용
                df = strategy_obj.apply(df)
                
                # 백테스팅 결과가 의미 있는지 확인
                signal_count = (df['signal'] != 0).sum()
                if signal_count == 0:
                    print("\n⚠️ 경고: 선택한 기간과 간격에서 거래 신호가 생성되지 않았습니다.")
                    print("다음 옵션을 시도해보세요:")
                    print(f"  1. 더 긴 기간 사용: -p 3m 또는 -p 6m")
                    print(f"  2. 다른 시간 간격 사용: -v minute60 또는 -v day")
                    print(f"  3. 현재 시장 조건에 더 적합한 다른 전략 시도")
                
                # 백테스팅 실행
                results = backtest_strategy(df, initial_capital)
                
                # 결과에 전략 정보 추가
                results['strategy'] = strategy_obj.name
                results['strategy_params'] = strategy_obj.params
                results['period'] = period  # 기간 정보 추가
                results['interval'] = interval  # 데이터 간격 정보 추가
                
                # 결과 출력
                print("\n백테스팅 결과:")
                print(f"전략: {strategy_obj.name}")
                print(f"기간: {results['start_date']} ~ {results['end_date']} ({results['total_days']}일)")
                print(f"초기 자본금: {results['initial_capital']:,.0f} KRW")
                print(f"최종 자본금: {results['final_capital']:,.0f} KRW")
                print(f"총 수익률: {results['total_return_pct']:.2f}%")
                print(f"연간 수익률: {results['annual_return_pct']:.2f}%")
                print(f"최대 낙폭: {results['max_drawdown_pct']:.2f}%")
                print(f"거래 횟수: {results['trade_count']}")
                
                # 거래 내역 세부 정보 출력 (선택적)
                print_detailed_trades = True  # 상세 거래 내역 출력 여부
                if print_detailed_trades and results['trade_history']:
                    print("\n주요 거래 내역:")
                    for i, trade in enumerate(results['trade_history']):
                        if i >= 5:  # 최대 5개만 출력
                            print(f"... 총 {len(results['trade_history'])}개 거래 중 일부만 표시")
                            break
                        
                        trade_type = "매수" if trade['type'] == 'buy' else "매도"
                        position_change = trade.get('position_change', 0)
                        position_str = f"포지션 변화: {position_change*100:.1f}%" if position_change else ""
                        
                        print(f"{trade['date'].strftime('%Y-%m-%d')} | {trade_type} | " +
                              f"가격: {trade['price']:,.0f} KRW | " +
                              f"수량: {trade.get('amount', 0):.8f} | {position_str}")
                
                # 그래프 생성 전 unicode minus 설정 다시 적용
                matplotlib.rcParams['axes.unicode_minus'] = False
                
                # 백테스팅 결과 시각화
                chart_path = plot_backtest_results(ticker, results)
                
                # 텔레그램 알림
                if enable_telegram:
                    # 결과 메시지 작성
                    params_str = ", ".join([f"{k}={v}" for k, v in strategy_obj.params.items()])
                    
                    # 메시지 생성과 전송을 분리된 모듈 함수 사용
                    result_message = get_telegram_backtest_message(ticker, strategy_obj.name, params_str, results)
                    
                    # 차트 전송
                    await send_telegram_chart(chart_path, result_message, enable_telegram, bot)
            except Exception as e:
                error_message = f"백테스팅 중 오류 발생: {e}"
                print(f"\n❌ {error_message}")
                if enable_telegram:
                    await send_telegram_message(f"❌ {error_message}", enable_telegram, bot)
        else:
            error_message = f"유효하지 않은 전략: {strategy}"
            print(error_message)
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
    
    # 데이터 조회
    try:
        # 기간에 맞게 데이터 조회 (백테스팅 함수 활용)
        df = get_backtest_data(ticker, period, interval)
        
        if df is not None and not df.empty:
            # 기본 통계 계산
            stats = {
                'start_date': df.index[0].strftime('%Y-%m-%d'),
                'end_date': df.index[-1].strftime('%Y-%m-%d'),
                'highest_price': df['high'].max(),
                'lowest_price': df['low'].min(),
                'volume': df['volume'].sum()
            }
            
            # 콘솔 출력
            print("\n기본 통계:")
            print(f"시작일: {stats['start_date']}")
            print(f"종료일: {stats['end_date']}")
            print(f"최고가: {stats['highest_price']:,.0f} KRW")
            print(f"최저가: {stats['lowest_price']:,.0f} KRW")
            print(f"총 거래량: {stats['volume']:,.0f}")
            
            # 차트 디렉토리 설정
            chart_dir = setup_chart_dir(CHART_SAVE_PATH)
            
            # 그래프 생성 전 unicode minus 설정 다시 적용
            matplotlib.rcParams['axes.unicode_minus'] = False
            
            # 차트 생성 - interval과 period 정보 전달
            chart_path = plot_price_chart(df, ticker, chart_dir=chart_dir, interval=interval, period=period)
            
            # 텔레그램 알림
            if enable_telegram:
                stats_message = get_telegram_analysis_message(ticker, stats)
                await send_telegram_chart(chart_path, stats_message, enable_telegram, bot)
        else:
            error_message = f"{ticker} 데이터 조회 실패"
            print(error_message)
            if enable_telegram:
                await send_telegram_message(f"❌ {error_message}", enable_telegram, bot)
    except Exception as e:
        error_message = f"{ticker} 분석 중 오류 발생: {e}"
        print(error_message)
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

async def main_async(args):
    # 명령줄 인자 추출
    enable_telegram = args.telegram
    enable_backtest = args.backtest
    strategy = args.strategy
    period = args.period
    initial_capital = args.invest
    enable_account = args.account
    coins = args.coins.split(',')
    interval = args.interval
    
    # 시각화 모듈 사용하여 차트 디렉토리 설정
    charts_dir = setup_chart_dir(CHART_SAVE_PATH)
    
    # 백테스팅 결과 디렉토리 생성
    if enable_backtest:
        backtest_results_dir = setup_chart_dir(BACKTEST_RESULT_PATH)
    
    # List of tickers to analyze - KRW 마켓 심볼로 변환
    tickers = [f"KRW-{coin}" for coin in coins]
    
    # 텔레그램 봇 설정
    bot = None
    if enable_telegram:
        # 환경 변수에서 텔레그램 설정 읽기
        TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
        
        # 텔레그램 봇 초기화
        if TELEGRAM_TOKEN:
            bot = Bot(token=TELEGRAM_TOKEN)
            print("텔레그램 봇이 설정되었습니다.")
        else:
            print("텔레그램 봇 토큰이 설정되지 않았습니다.")
    
    # 계좌 정보 조회 모드
    if enable_account:
        await check_account(bot, enable_telegram)
        return
    
    if enable_telegram:
        async with bot:
            if enable_backtest:
                await send_telegram_message("🚀 암호화폐 백테스팅 시작...", enable_telegram, bot)
                
                # 백테스팅 실행
                for ticker in tickers:
                    await run_backtest(bot, ticker, strategy, period, initial_capital, enable_telegram, interval)
                
                await send_telegram_message("✅ 백테스팅 완료!", enable_telegram, bot)
            else:
                await send_telegram_message("🚀 암호화폐 분석 시작...", enable_telegram, bot)
                
                # Analyze each ticker
                for ticker in tickers:
                    await analyze_ticker(bot, ticker, enable_telegram, interval, period)
                
                await send_telegram_message("✅ 분석 완료!", enable_telegram, bot)
    else:
        # 백테스팅 모드일 경우
        if enable_backtest:
            print("🚀 암호화폐 백테스팅 시작...")
            
            # 백테스팅 실행
            for ticker in tickers:
                await run_backtest(None, ticker, strategy, period, initial_capital, enable_telegram, interval)
            
            print("✅ 백테스팅 완료!")
        else:
            print("🚀 암호화폐 분석 시작...")
            
            # Run without telegram notifications
            for ticker in tickers:
                await analyze_ticker(None, ticker, enable_telegram, interval, period)
            
            print("✅ 분석 완료!")

def main():
    # 명령줄 인자 파싱
    args = parse_args()
    
    # Run the async main function
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main() 