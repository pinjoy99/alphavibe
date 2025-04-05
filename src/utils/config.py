"""
환경 변수 관리 모듈
"""
import os
from typing import Any, Optional
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 관련 환경 변수
UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')

# 알림 관련 환경 변수
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

# 기본 설정
DEFAULT_INTERVAL = os.getenv('DEFAULT_INTERVAL', 'day')
DEFAULT_COUNT = int(os.getenv('DEFAULT_COUNT', '100'))
CHART_DIR = os.getenv('CHART_DIR', 'charts')

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