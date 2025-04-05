import os
from typing import Optional
from telegram import Bot
import asyncio
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 텔레그램 설정
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

async def send_message(message: str, enable_telegram: bool = True, bot: Optional[Bot] = None) -> None:
    """
    텔레그램으로 메시지 전송
    
    Parameters:
        message (str): 전송할 메시지
        enable_telegram (bool): 텔레그램 전송 활성화 여부
        bot (Optional[Bot]): 텔레그램 봇 객체 (None인 경우 새로 생성)
    """
    if not enable_telegram or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    # 봇이 전달되지 않은 경우 새로 생성
    close_bot = False
    if bot is None:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        close_bot = True
    
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
    except Exception as e:
        print(f"텔레그램 메시지 전송 실패: {e}")
    
    # 새로 생성한 봇은 종료
    if close_bot:
        await bot.close()

async def send_chart(chart_path: str, caption: str = "", enable_telegram: bool = True, bot: Optional[Bot] = None) -> None:
    """
    텔레그램으로 차트 이미지 전송
    
    Parameters:
        chart_path (str): 차트 이미지 파일 경로
        caption (str): 이미지 캡션
        enable_telegram (bool): 텔레그램 전송 활성화 여부
        bot (Optional[Bot]): 텔레그램 봇 객체 (None인 경우 새로 생성)
    """
    if not enable_telegram or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    # 봇이 전달되지 않은 경우 새로 생성
    close_bot = False
    if bot is None:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        close_bot = True
    
    try:
        with open(chart_path, 'rb') as chart:
            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=chart,
                caption=caption,
                parse_mode='HTML'
            )
    except Exception as e:
        print(f"텔레그램 차트 전송 실패: {e}")
        # 파일 경로 오류인 경우 추가 정보 출력
        if "No such file or directory" in str(e):
            print(f"파일을 찾을 수 없습니다: {chart_path}")
    
    # 새로 생성한 봇은 종료
    if close_bot:
        await bot.close()

# 백테스팅 결과 메시지 템플릿
def get_backtest_result_message(ticker: str, strategy_name: str, params_str: str, results: dict) -> str:
    """
    백테스팅 결과 메시지 생성
    
    Parameters:
        ticker (str): 종목 심볼
        strategy_name (str): 전략 이름
        params_str (str): 파라미터 문자열
        results (dict): 백테스팅 결과 데이터
        
    Returns:
        str: 포맷된 결과 메시지
    """
    return f"""
📊 <b>{ticker} 백테스팅 결과</b>

🔹 <b>전략:</b> {strategy_name} {params_str}
📅 <b>기간:</b> {results['start_date']} ~ {results['end_date']} ({results['total_days']}일)
💰 <b>초기 자본금:</b> {results['initial_capital']:,.0f} KRW
💰 <b>최종 자본금:</b> {results['final_capital']:,.0f} KRW
📈 <b>총 수익률:</b> {results['total_return_pct']:.2f}%
📈 <b>연간 수익률:</b> {results['annual_return_pct']:.2f}%
📉 <b>최대 낙폭:</b> {results['max_drawdown_pct']:.2f}%
🔄 <b>거래 횟수:</b> {results['trade_count']}
"""

# 분석 결과 메시지 템플릿
def get_analysis_message(ticker: str, stats: dict) -> str:
    """
    가격 분석 결과 메시지 생성
    
    Parameters:
        ticker (str): 종목 심볼
        stats (dict): 분석 통계 데이터
        
    Returns:
        str: 포맷된 결과 메시지
    """
    return f"""
📊 <b>{ticker} 분석 결과</b>

📅 기간: {stats['start_date']} ~ {stats['end_date']}
💰 최고가: {stats['highest_price']:,} KRW
💰 최저가: {stats['lowest_price']:,} KRW
📈 거래량: {stats['volume']:,}
""" 