# 환경 변수 설정

이 애플리케이션에서는 민감한 정보만 `.env` 파일에 저장하고, 일반적인 설정값은 모두 `src/utils/config.py` 파일에서 직접 관리합니다.

## 환경 변수 파일 설정 방법

1. `.env.example` 파일을 `.env`로 복사합니다:
   ```
   cp .env.example .env
   ```

2. `.env` 파일을 열어 필요한 민감한 정보를 입력합니다:
   ```
   # Upbit API 키 설정 (필수)
   UPBIT_ACCESS_KEY=your_access_key_here
   UPBIT_SECRET_KEY=your_secret_key_here

   # 텔레그램 설정 (선택사항)
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here
   ```

3. 민감한 정보 설명:

   | 환경 변수 | 설명 |
   |-----------|------|
   | UPBIT_ACCESS_KEY | Upbit API 액세스 키 |
   | UPBIT_SECRET_KEY | Upbit API 시크릿 키 |
   | TELEGRAM_BOT_TOKEN | 텔레그램 봇 토큰 |
   | TELEGRAM_CHAT_ID | 텔레그램 채팅 ID |

4. 일반 설정값 변경 방법:

   모든 일반 설정값은 `src/utils/config.py` 파일에서 직접 수정할 수 있습니다. 주요 설정값은 다음과 같습니다:

   | 설정 | 설명 | 기본값 |
   |------|------|--------|
   | CHART_SAVE_PATH | 차트 이미지 저장 경로 | results/analysis |
   | BACKTEST_RESULT_PATH | 백테스트 결과 저장 경로 | results/strategy_results |
   | DEFAULT_INTERVAL | 기본 시간 간격 | day |
   | DEFAULT_COUNT | 조회할 데이터 개수 | 100 |
   | DEFAULT_COINS | 기본 분석 코인 리스트 | BTC,ETH,XRP |
   | LOG_LEVEL | 로그 레벨 | INFO |
   | ENABLE_TELEGRAM | 텔레그램 알림 활성화 여부 | False |
   | DEFAULT_INITIAL_CAPITAL | 백테스팅 기본 초기 자본 | 1,000,000원 |
   | DEFAULT_BACKTEST_PERIOD | 백테스팅 기본 기간 | 3개월 |
   | COMMISSION_RATE | 거래 수수료율 | 0.05% |
   | SMALL_AMOUNT_THRESHOLD | 소액 코인 기준값 | 500원 |
   | TOP_COIN_COUNT | 상위 코인 표시 개수 | 5개 |

**참고**: `setup.sh` 스크립트 실행 시 `.env` 파일이 없는 경우 자동으로 `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다. 