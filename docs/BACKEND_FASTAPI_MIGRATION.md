# AlphaVibe 백엔드 FastAPI 마이그레이션 및 전략 연동/버그 수정 내역

## 1. FastAPI 기반 백엔드 구조 확립
- `src/api/main.py`에 FastAPI 앱 구조, CORS, 로깅, .env 로드, 헬스체크/백테스트/전략목록 엔드포인트 구현
- requirements.txt에 fastapi, uvicorn, python-dotenv 등 필수 패키지 포함

## 2. 전략 목록 동적 연동
- `/api/strategies` 엔드포인트가 하드코딩 대신 `src/strategies/strategy_registry.py`의 `StrategyRegistry.get_available_strategies()`를 통해 동적으로 전략 목록 제공
- StrategyRegistry가 strategies 디렉토리 내 CODE/NAME/DESCRIPTION이 정의된 모든 전략 클래스를 자동 등록

## 3. 백테스트 엔드포인트의 전략 클래스 동적 선택
- `src/backtest/backtest_engine.py`의 `run_backtest()`에서 strategy_name에 따라 StrategyRegistry에서 전략 클래스를 동적으로 가져오도록 변경
- 내부 테스트용 SMAStrategy, MACDStrategy 클래스에서 CODE 등 메타데이터 속성 제거(등록 충돌 방지)

## 4. SMAStrategy 파라미터(class variable) 인식 문제 해결
- `src/strategies/sma_strategy_bt.py`의 클래스명을 `SMAStrategyBT` → `SMAStrategy`로 변경 (CODE="sma"와 일치)
- short_window, long_window를 `short_window: ClassVar[int] = 10`과 같이 명확히 class variable로 선언
- StrategyRegistry가 등록하는 SMAStrategy가 실제로 src/strategies/sma_strategy_bt.py의 클래스임을 확인

## 5. 기타 충돌/ImportError 수정
- `src/strategies/__init__.py`에서 `from src.strategies.sma_strategy_bt import SMAStrategy`로 변경
- 불필요한/중복된 전략 클래스 등록 방지

## 6. 테스트 및 검증
- 서버 기동 후 `/api/health`, `/api/strategies`, `/api/backtest` 엔드포인트를 curl로 직접 테스트
- 백테스트 요청 시 SMAStrategy의 파라미터가 정상적으로 인식되고, 실제 전략 실행 및 매수/매도 신호 발생 확인

---

이 문서는 2025-04-16 기준 FastAPI 기반 백엔드 구조 및 전략 연동, 파라미터 인식 문제 해결 과정을 기록한 변경 이력입니다.
