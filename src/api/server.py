from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
from src.backtest import run_backtest_bt
from src.api.upbit_api import get_backtest_data
from src.strategies.strategy_registry import StrategyRegistry
import pandas as pd
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI(
    title="AlphaVibe API",
    description="암호화폐 거래 전략 백테스팅 API",
    version="1.0.0"
)

# CORS 미들웨어 설정
origins = [
    "http://localhost:3000",  # React 개발 서버
    "http://localhost:8001",  # FastAPI 서버
    os.getenv("FRONTEND_URL", "http://localhost:3000")  # 프로덕션 프론트엔드 URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 백테스팅 요청 모델
class BacktestRequest(BaseModel):
    ticker: str
    period: str
    strategy: str
    initial_capital: float
    params: Optional[Dict[str, Any]] = None

# 전략 정보 응답 모델
class StrategyInfo(BaseModel):
    code: str
    name: str
    description: str
    params: List[Dict[str, Any]]

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 사용 가능한 전략 목록 조회
@app.get("/api/strategies", response_model=List[StrategyInfo])
async def get_strategies():
    try:
        strategies = StrategyRegistry.get_available_strategies()
        return strategies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 백테스팅 엔드포인트
@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    try:
        # 데이터 조회
        df = get_backtest_data(request.ticker, request.period, "minute60")
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="데이터를 가져올 수 없습니다.")

        # 전략 클래스 가져오기
        strategy_class = None
        for strategy in StrategyRegistry.get_available_strategies():
            if strategy["code"] == request.strategy:
                strategy_class = strategy.get("class")
                break
        
        if strategy_class is None:
            raise HTTPException(status_code=400, detail=f"전략을 찾을 수 없습니다: {request.strategy}")

        # 백테스팅 실행
        results = run_backtest_bt(
            df=df,
            strategy_class=strategy_class,
            initial_capital=request.initial_capital,
            strategy_name=f"{request.strategy.upper()} Strategy",
            ticker=request.ticker,
            **(request.params or {})
        )

        # 차트 데이터 포맷팅
        chart_data = []
        for index, row in df.iterrows():
            data_point = {
                "date": index.strftime("%Y-%m-%d"),
                "price": float(row["close"]),
                "volume": float(row["volume"]),
                "portfolio": float(results["equity_curve"].get(index, 0))
            }
            
            # 전략별 지표 추가
            if request.strategy == "sma":
                data_point.update({
                    "shortSMA": float(row.get("short_sma", 0)),
                    "longSMA": float(row.get("long_sma", 0))
                })
            elif request.strategy == "macd":
                data_point.update({
                    "macd": float(row.get("macd", 0)),
                    "signal": float(row.get("signal", 0)),
                    "histogram": float(row.get("histogram", 0))
                })
            
            # 매수/매도 신호 추가
            if index in results.get("buy_signals", []):
                data_point["buySignal"] = float(row["close"])
            if index in results.get("sell_signals", []):
                data_point["sellSignal"] = float(row["close"])
                
            chart_data.append(data_point)

        return {
            "status": "success",
            "message": "백테스팅이 성공적으로 완료되었습니다.",
            "data": chart_data,
            "summary": {
                "initialCapital": float(request.initial_capital),
                "finalCapital": float(results["final_asset"]),
                "totalReturn": float(results["return_pct"]),
                "maxDrawdown": float(results["max_drawdown"]),
                "totalTrades": int(results["total_trades"]),
                "winRate": float(results["win_rate"]),
                "profitLossRatio": float(results.get("profit_loss_ratio", 0))
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 