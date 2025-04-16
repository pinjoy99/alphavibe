from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from src.backtest.backtest_engine import run_backtest
from src.api.upbit_api import get_backtest_data

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI(title="AlphaVibe Backend", version="1.0.0")

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 origin을 지정해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 모델 정의
class BacktestRequest(BaseModel):
    ticker: str
    period: str
    strategy: str
    initial_capital: float
    params: Optional[Dict[str, Any]] = None

class BacktestDataPoint(BaseModel):
    date: str
    price: float
    shortSMA: float
    longSMA: float
    volume: float
    portfolio: float
    buySignal: Optional[float] = None
    sellSignal: Optional[float] = None

class BacktestSummary(BaseModel):
    initialCapital: float
    finalCapital: float
    totalReturn: float
    maxDrawdown: float
    totalTrades: int
    winRate: float
    profitLossRatio: float

class BacktestResponse(BaseModel):
    data: List[BacktestDataPoint]
    summary: BacktestSummary

# 헬스체크 엔드포인트
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# 백테스트 엔드포인트
@app.post("/api/backtest", response_model=BacktestResponse)
async def run_backtest_api(request: BacktestRequest):
    try:
        logger.info(f"백테스트 요청 받음: {request}")
        
        # 데이터 조회
        df = get_backtest_data(request.ticker, request.period)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")
            
        # 백테스팅 실행
        results = run_backtest(
            df=df,
            strategy_name=request.strategy,
            initial_capital=request.initial_capital,
            params=request.params
        )
        
        # 응답 생성
        response = BacktestResponse(
            data=[BacktestDataPoint(**point) for point in results['data']],
            summary=BacktestSummary(**results['summary'])
        )
        
        return response

    except ValueError as e:
        logger.error(f"잘못된 요청: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"백테스트 중 에러 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 사용 가능한 전략 목록 조회
from src.strategies.strategy_registry import StrategyRegistry

@app.get("/api/strategies")
async def get_strategies():
    try:
        strategies = StrategyRegistry.get_available_strategies()
        return {"strategies": strategies}
    except Exception as e:
        logger.error(f"전략 목록 조회 중 에러 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
