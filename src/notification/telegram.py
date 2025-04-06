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

# 텔레그램 설정 디버깅 정보
print(f"텔레그램 설정 - 토큰: {'설정됨' if TELEGRAM_BOT_TOKEN else '설정되지 않음'}, 채팅 ID: {'설정됨' if TELEGRAM_CHAT_ID else '설정되지 않음'}")

async def send_message(message: str, enable_telegram: bool = True, bot: Optional[Bot] = None) -> None:
    """
    텔레그램으로 메시지 전송
    
    Parameters:
        message (str): 전송할 메시지
        enable_telegram (bool): 텔레그램 전송 활성화 여부
        bot (Optional[Bot]): 텔레그램 봇 객체 (None인 경우 새로 생성)
    """
    if not enable_telegram:
        print("텔레그램 알림이 비활성화되어 있습니다.")
        return
        
    if not TELEGRAM_BOT_TOKEN:
        print("텔레그램 봇 토큰이 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
        
    if not TELEGRAM_CHAT_ID:
        print("텔레그램 채팅 ID가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
    
    # 봇이 전달되지 않은 경우 새로 생성
    close_bot = False
    if bot is None:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        close_bot = True
    
    try:
        print(f"텔레그램 메시지 전송 시도: {message[:50]}...")
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
        print("텔레그램 메시지 전송 성공")
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
    if not enable_telegram:
        print("텔레그램 알림이 비활성화되어 있습니다.")
        return
        
    if not TELEGRAM_BOT_TOKEN:
        print("텔레그램 봇 토큰이 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
        
    if not TELEGRAM_CHAT_ID:
        print("텔레그램 채팅 ID가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
    
    # 차트 파일 존재 확인
    if not os.path.exists(chart_path):
        print(f"차트 파일이 존재하지 않습니다: {chart_path}")
        return
    
    # 봇이 전달되지 않은 경우 새로 생성
    close_bot = False
    if bot is None:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        close_bot = True
    
    try:
        print(f"텔레그램 차트 전송 시도: {chart_path}")
        with open(chart_path, 'rb') as chart:
            await bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=chart,
                caption=caption,
                parse_mode='HTML'
            )
        print("텔레그램 차트 전송 성공")
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
    try:
        # 필수 키가 없는 경우 대체 키 또는 기본값 사용
        start_date = results.get('start_date', '정보 없음')
        end_date = results.get('end_date', '정보 없음')
        total_days = results.get('total_days', 0)
        initial_capital = results.get('initial_capital', 0)
        
        # final_capital이 없으면 final_asset을 사용, 둘 다 없으면 initial_capital 사용
        final_capital = results.get('final_capital', results.get('final_asset', initial_capital))
        
        # 수익률 관련 값
        total_return_pct = results.get('total_return_pct', results.get('return_pct', 0))
        annual_return_pct = results.get('annual_return_pct', 0)
        max_drawdown_pct = results.get('max_drawdown_pct', 0)
        
        # 거래 횟수
        trade_count = results.get('trade_count', results.get('total_trades', 0))
        
        return f"""
📊 <b>{ticker} 백테스팅 결과</b>

🔹 <b>전략:</b> {strategy_name} {params_str}
📅 <b>기간:</b> {start_date} ~ {end_date} ({total_days}일)
💰 <b>초기 자본금:</b> {initial_capital:,.0f} KRW
💰 <b>최종 자본금:</b> {final_capital:,.0f} KRW
📈 <b>총 수익률:</b> {total_return_pct:.2f}%
📈 <b>연간 수익률:</b> {annual_return_pct:.2f}%
📉 <b>최대 낙폭:</b> {max_drawdown_pct:.2f}%
🔄 <b>거래 횟수:</b> {trade_count}
"""
    except Exception as e:
        print(f"백테스트 결과 메시지 생성 중 오류 발생: {e}")
        print(f"결과 데이터: {results}")
        # 기본 메시지 반환
        return f"""
📊 <b>{ticker} 백테스팅 결과</b>

🔹 <b>전략:</b> {strategy_name} {params_str}
❌ <b>결과 데이터 처리 중 오류가 발생했습니다.</b>
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