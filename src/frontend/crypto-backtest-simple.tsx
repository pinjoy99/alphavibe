import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ComposedChart, BarChart, Bar, Area, Scatter, ReferenceLine } from 'recharts';

// 메인 컴포넌트
const CryptoBacktestApp = () => {
  // 상태 관리
  const [ticker, setTicker] = useState('BTC');
  const [period, setPeriod] = useState('3m');
  const [strategy, setStrategy] = useState('sma');
  const [initialCapital, setInitialCapital] = useState(10000000);
  const [isLoading, setIsLoading] = useState(false);
  const [backtestResults, setBacktestResults] = useState(null);

  // 테스트 데이터
  const demoData = [
    { date: '2023-01-01', price: 30000, shortSMA: 29000, longSMA: 28000, volume: 1200, portfolio: 10000000 },
    { date: '2023-01-02', price: 31000, shortSMA: 29500, longSMA: 28200, volume: 1300, portfolio: 10333333 },
    { date: '2023-01-03', price: 32000, shortSMA: 30000, longSMA: 28500, volume: 1500, portfolio: 10666667, buySignal: 32000 },
    { date: '2023-01-04', price: 32500, shortSMA: 30500, longSMA: 28800, volume: 1400, portfolio: 10833333 },
    { date: '2023-01-05', price: 32000, shortSMA: 31000, longSMA: 29000, volume: 1350, portfolio: 10666667 },
    { date: '2023-01-06', price: 31000, shortSMA: 31200, longSMA: 29200, volume: 1250, portfolio: 10333333 },
    { date: '2023-01-07', price: 30000, shortSMA: 31000, longSMA: 29500, volume: 1300, portfolio: 10000000, sellSignal: 30000 },
    { date: '2023-01-08', price: 29500, shortSMA: 30700, longSMA: 29600, volume: 1200, portfolio: 9833333 },
    { date: '2023-01-09', price: 29000, shortSMA: 30300, longSMA: 29700, volume: 1150, portfolio: 9666667 },
    { date: '2023-01-10', price: 30000, shortSMA: 30100, longSMA: 29800, volume: 1250, portfolio: 10000000, buySignal: 30000 },
    { date: '2023-01-11', price: 31000, shortSMA: 30000, longSMA: 29900, volume: 1300, portfolio: 10333333 },
    { date: '2023-01-12', price: 32000, shortSMA: 30200, longSMA: 30000, volume: 1400, portfolio: 10666667 },
    { date: '2023-01-13', price: 33000, shortSMA: 30500, longSMA: 30100, volume: 1500, portfolio: 11000000 },
    { date: '2023-01-14', price: 32500, shortSMA: 30800, longSMA: 30200, volume: 1400, portfolio: 10833333, sellSignal: 32500 },
    { date: '2023-01-15', price: 32000, shortSMA: 31000, longSMA: 30300, volume: 1350, portfolio: 10666667 }
  ];

  // 백테스팅 실행
  const runBacktest = () => {
    setIsLoading(true);
    
    // 실제로는 여기서 API 호출을 통해 백테스팅 실행
    
    // 간단한 데모를 위해 고정된 결과값 사용
    setTimeout(() => {
      setBacktestResults({
        data: demoData,
        summary: {
          initialCapital: initialCapital,
          finalCapital: 10666667,
          totalReturn: 6.67,
          maxDrawdown: 3.33,
          totalTrades: 4,
          winRate: 75.0,
          profitLossRatio: 2.5
        }
      });
      setIsLoading(false);
    }, 1000);
  };

  // 포맷 함수
  const formatNumber = (number) => {
    return new Intl.NumberFormat('ko-KR').format(number);
  };

  // 결과 요약 컴포넌트
  const ResultSummary = ({ summary }) => {
    if (!summary) return null;

    const {
      initialCapital,
      finalCapital,
      totalReturn,
      maxDrawdown,
      totalTrades,
      winRate,
      profitLossRatio
    } = summary;

    return (
      <div className="bg-gray-100 p-4 rounded-lg mb-4">
        <h3 className="text-xl font-bold mb-4">백테스팅 결과 요약</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-3 rounded shadow">
            <p className="text-sm text-gray-500">초기 자본금</p>
            <p className="text-lg font-bold">{formatNumber(initialCapital)} 원</p>
          </div>
          <div className="bg-white p-3 rounded shadow">
            <p className="text-sm text-gray-500">최종 자본금</p>
            <p className="text-lg font-bold">{formatNumber(finalCapital)} 원</p>
          </div>
          <div className="bg-white p-3 rounded shadow">
            <p className="text-sm text-gray-500">총 수익률</p>
            <p className={`text-lg font-bold ${totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%
            </p>
          </div>
          <div className="bg-white p-3 rounded shadow">
            <p className="text-sm text-gray-500">최대 낙폭</p>
            <p className="text-lg font-bold text-red-600">-{maxDrawdown.toFixed(2)}%</p>
          </div>
          <div className="bg-white p-3 rounded shadow">
            <p className="text-sm text-gray-500">총 거래 횟수</p>
            <p className="text-lg font-bold">{totalTrades}회</p>
          </div>
          <div className="bg-white p-3 rounded shadow">
            <p className="text-sm text-gray-500">승률</p>
            <p className="text-lg font-bold">{winRate.toFixed(2)}%</p>
          </div>
        </div>
      </div>
    );
  };

  // 가격 차트 컴포넌트
  const PriceChart = ({ data }) => {
    return (
      <div className="bg-white p-4 rounded-lg shadow mb-4">
        <h3 className="text-lg font-semibold mb-4">가격 & 지표 차트</h3>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
            <XAxis dataKey="date" />
            <YAxis 
              yAxisId="left"
              orientation="left"
              domain={['auto', 'auto']}
              tickFormatter={(tick) => formatNumber(tick)}
            />
            <Tooltip formatter={(value) => formatNumber(value)} />
            <Legend />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="price" 
              name="가격" 
              stroke="#2196F3" 
              dot={false} 
              strokeWidth={2}
            />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="shortSMA" 
              name="단기 이동평균(10)" 
              stroke="#FF9800" 
              dot={false} 
              strokeWidth={1.5}
            />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="longSMA" 
              name="장기 이동평균(30)" 
              stroke="#4CAF50" 
              dot={false} 
              strokeWidth={1.5}
            />
            <Scatter 
              yAxisId="left"
              dataKey="buySignal" 
              name="매수 신호" 
              fill="#4CAF50" 
              shape="triangle" 
              size={100}
            />
            <Scatter 
              yAxisId="left"
              dataKey="sellSignal" 
              name="매도 신호" 
              fill="#F44336" 
              shape="triangle" 
              size={100}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    );
  };

  // 거래량 차트 컴포넌트
  const VolumeChart = ({ data }) => {
    return (
      <div className="bg-white p-4 rounded-lg shadow mb-4">
        <h3 className="text-lg font-semibold mb-4">거래량 차트</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
            <XAxis dataKey="date" />
            <YAxis tickFormatter={(tick) => formatNumber(tick)} />
            <Tooltip formatter={(value) => formatNumber(value)} />
            <Bar dataKey="volume" name="거래량" fill="#64B5F6" opacity={0.8} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  // 포트폴리오 차트 컴포넌트
  const PortfolioChart = ({ data }) => {
    return (
      <div className="bg-white p-4 rounded-lg shadow mb-4">
        <h3 className="text-lg font-semibold mb-4">포트폴리오 가치 변화</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data} margin={{ top: 10, right: 30, left: 20, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
            <XAxis dataKey="date" />
            <YAxis tickFormatter={(tick) => formatNumber(tick)} />
            <Tooltip formatter={(value) => formatNumber(value)} />
            <Line 
              type="monotone" 
              dataKey="portfolio" 
              name="포트폴리오 가치" 
              stroke="#FF5722" 
              dot={false} 
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">암호화폐 백테스팅 도구</h1>
      
      {/* 설정 패널 */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-xl font-semibold mb-4">백테스팅 설정</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          {/* 코인 선택 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">코인</label>
            <select 
              className="w-full p-2 border border-gray-300 rounded"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
            >
              <option value="BTC">Bitcoin (BTC)</option>
              <option value="ETH">Ethereum (ETH)</option>
              <option value="XRP">Ripple (XRP)</option>
              <option value="SOL">Solana (SOL)</option>
              <option value="ADA">Cardano (ADA)</option>
            </select>
          </div>
          
          {/* 기간 선택 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">기간</label>
            <select 
              className="w-full p-2 border border-gray-300 rounded"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              <option value="1w">1주</option>
              <option value="1m">1개월</option>
              <option value="3m">3개월</option>
              <option value="6m">6개월</option>
              <option value="1y">1년</option>
            </select>
          </div>
          
          {/* 전략 선택 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">전략</label>
            <select 
              className="w-full p-2 border border-gray-300 rounded"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            >
              <option value="sma">이동평균선 (SMA)</option>
              <option value="macd">MACD</option>
              <option value="rsi">RSI</option>
              <option value="bb">볼린저 밴드</option>
            </select>
          </div>
          
          {/* 초기 자본 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">초기 자본</label>
            <input 
              type="number" 
              className="w-full p-2 border border-gray-300 rounded"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              min="100000"
              step="1000000"
            />
          </div>
        </div>
        
        {/* SMA 전략 파라미터 */}
        {strategy === 'sma' && (
          <div className="mb-4 p-4 bg-gray-50 rounded">
            <h3 className="text-md font-medium mb-2">SMA 전략 파라미터</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-700 mb-1">단기 이동평균 기간</label>
                <input 
                  type="number" 
                  className="w-full p-2 border border-gray-300 rounded"
                  defaultValue={10}
                  min="2"
                  max="50"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">장기 이동평균 기간</label>
                <input 
                  type="number" 
                  className="w-full p-2 border border-gray-300 rounded"
                  defaultValue={30}
                  min="5"
                  max="200"
                />
              </div>
            </div>
          </div>
        )}
        
        {/* RSI 전략 파라미터 */}
        {strategy === 'rsi' && (
          <div className="mb-4 p-4 bg-gray-50 rounded">
            <h3 className="text-md font-medium mb-2">RSI 전략 파라미터</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-700 mb-1">RSI 기간</label>
                <input 
                  type="number" 
                  className="w-full p-2 border border-gray-300 rounded"
                  defaultValue={14}
                  min="2"
                  max="50"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">과매수 기준</label>
                <input 
                  type="number" 
                  className="w-full p-2 border border-gray-300 rounded"
                  defaultValue={70}
                  min="50"
                  max="90"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">과매도 기준</label>
                <input 
                  type="number" 
                  className="w-full p-2 border border-gray-300 rounded"
                  defaultValue={30}
                  min="10"
                  max="50"
                />
              </div>
            </div>
          </div>
        )}
        
        <button 
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          onClick={runBacktest}
          disabled={isLoading}
        >
          {isLoading ? '백테스팅 진행 중...' : '백테스팅 실행'}
        </button>
      </div>
      
      {/* 결과 영역 */}
      {backtestResults && (
        <div>
          <ResultSummary summary={backtestResults.summary} />
          <PriceChart data={backtestResults.data} />
          <VolumeChart data={backtestResults.data} />
          <PortfolioChart data={backtestResults.data} />
        </div>
      )}
    </div>
  );
};

export default CryptoBacktestApp;
