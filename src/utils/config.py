"""
환경 변수 및 구성 설정 관리 모듈
민감한 정보만 .env 파일에서 로드하고 나머지 설정은 이 파일에서 직접 관리합니다.
"""
import os
from typing import Any, Optional
from dotenv import load_dotenv

# 환경 변수 로드 (.env 파일에는 민감한 정보만 포함됨)
load_dotenv()

#-----------------------------------------------------
# 애플리케이션 설정 (코드에서 직접 관리)
#-----------------------------------------------------

# 경로 설정
CHART_SAVE_PATH = 'results/analysis'
BACKTEST_CHART_PATH = 'results/backtest_charts'

# 하위 호환성을 위한 별칭
CHART_DIR = CHART_SAVE_PATH  # 이전 코드와의 호환성 유지

# 데이터 조회 설정
DEFAULT_INTERVAL = 'day'
DEFAULT_COUNT = 100
DEFAULT_COINS = 'BTC,ETH,XRP'  # 기본 분석 코인 리스트

# 로그 설정
LOG_LEVEL = 'INFO'

# 텔레그램 활성화 설정
ENABLE_TELEGRAM = False

# 백테스팅 설정
DEFAULT_INITIAL_CAPITAL = 1000000  # 백테스팅 기본 초기 자본 (100만원)
DEFAULT_BACKTEST_PERIOD = '3m'     # 백테스팅 기본 기간 (3개월)
COMMISSION_RATE = 0.0005           # 거래 수수료율 (0.05%)

# 계좌 정보 설정
SMALL_AMOUNT_THRESHOLD = 500       # 소액 코인 기준값 (500원 미만)
TOP_COIN_COUNT = 5                 # 상위 코인 표시 개수

#-----------------------------------------------------
# 민감한 정보 (.env 파일에서 로드)
#-----------------------------------------------------

# API 관련 환경 변수
UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')

# 알림 관련 환경 변수
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 기타 알림 서비스 설정 (사용하지 않는 경우 None)
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

def get_env(key: str, default: Optional[Any] = None) -> Any:
    """
    환경 변수를 가져오는 헬퍼 함수
    
    Parameters:
        key (str): 환경 변수 키
        default (Optional[Any]): 환경 변수가 없을 때 기본값
        
    Returns:
        Any: 환경 변수 값 또는 기본값
    """
    return os.getenv(key, default) 