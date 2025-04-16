"""
백테스팅 엔진 테스트

백테스팅 엔진 및 결과 캐싱 기능을 테스트하는 케이스를 제공합니다.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.backtest.backtest_engine import run_backtest
from src.utils.cache_manager import CacheManager
import os

@pytest.fixture
def sample_data():
    """테스트용 샘플 데이터 생성"""
    dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
    data = {
        'Open': np.random.randn(10) * 1000 + 30000,  # BTC 가격 범위
        'High': np.random.randn(10) * 1000 + 31000,
        'Low': np.random.randn(10) * 1000 + 29000,
        'Close': np.random.randn(10) * 1000 + 30000,
        'Volume': np.random.rand(10) * 100
    }
    df = pd.DataFrame(data, index=dates)
    return df

@pytest.fixture
def cache_manager():
    """테스트용 캐시 매니저 생성"""
    cache_dir = "tests/temp_cache"
    manager = CacheManager(cache_dir)
    yield manager
    # 테스트 후 정리
    if os.path.exists(cache_dir):
        for file in os.listdir(cache_dir):
            os.remove(os.path.join(cache_dir, file))
        os.rmdir(cache_dir)

def test_run_backtest_basic(sample_data):
    """기본 백테스팅 테스트"""
    # SMA 전략으로 백테스팅
    result = run_backtest(
        df=sample_data,
        strategy_name='sma',
        initial_capital=10000000,
        params={'short_window': 5, 'long_window': 10}
    )
    
    # 결과 구조 확인
    assert 'data' in result
    assert 'summary' in result
    assert isinstance(result['data'], list)
    assert isinstance(result['summary'], dict)
    
    # 요약 정보 확인
    summary = result['summary']
    assert 'initialCapital' in summary
    assert 'finalCapital' in summary
    assert 'totalReturn' in summary
    assert 'maxDrawdown' in summary
    assert 'totalTrades' in summary
    assert 'winRate' in summary

def test_run_backtest_caching(sample_data):
    """백테스팅 결과 캐싱 테스트"""
    # 첫 번째 백테스팅
    result1 = run_backtest(
        df=sample_data,
        strategy_name='sma',
        initial_capital=10000000,
        params={'short_window': 5, 'long_window': 10}
    )
    
    # 두 번째 백테스팅 (캐시에서 로드되어야 함)
    result2 = run_backtest(
        df=sample_data,
        strategy_name='sma',
        initial_capital=10000000,
        params={'short_window': 5, 'long_window': 10}
    )
    
    # 결과가 동일한지 확인
    assert result1['summary'] == result2['summary']
    assert len(result1['data']) == len(result2['data'])

def test_run_backtest_different_params(sample_data):
    """다른 파라미터로 백테스팅 테스트"""
    # SMA 전략 (5, 10)
    result1 = run_backtest(
        df=sample_data,
        strategy_name='sma',
        initial_capital=10000000,
        params={'short_window': 5, 'long_window': 10}
    )
    
    # SMA 전략 (10, 20)
    result2 = run_backtest(
        df=sample_data,
        strategy_name='sma',
        initial_capital=10000000,
        params={'short_window': 10, 'long_window': 20}
    )
    
    # MACD 전략
    result3 = run_backtest(
        df=sample_data,
        strategy_name='macd',
        initial_capital=10000000
    )
    
    # 결과가 서로 다른지 확인
    assert result1['summary'] != result2['summary']
    assert result1['summary'] != result3['summary']
    assert result2['summary'] != result3['summary']

def test_run_backtest_invalid_strategy(sample_data):
    """잘못된 전략 테스트"""
    with pytest.raises(ValueError):
        run_backtest(
            df=sample_data,
            strategy_name='invalid_strategy',
            initial_capital=10000000
        )

def test_run_backtest_data_consistency(sample_data):
    """데이터 일관성 테스트"""
    result = run_backtest(
        df=sample_data,
        strategy_name='sma',
        initial_capital=10000000,
        params={'short_window': 5, 'long_window': 10}
    )
    
    # 데이터 포인트 확인
    for point in result['data']:
        assert 'date' in point
        assert 'price' in point
        assert 'volume' in point
        assert 'portfolio' in point
        assert isinstance(point['date'], str)
        assert isinstance(point['price'], (int, float))
        assert isinstance(point['volume'], (int, float))
        assert isinstance(point['portfolio'], (int, float))

def test_run_backtest_performance(sample_data):
    """성능 테스트"""
    import time
    
    # 첫 번째 실행 (캐시 없음)
    start_time = time.time()
    run_backtest(
        df=sample_data,
        strategy_name='sma',
        initial_capital=10000000,
        params={'short_window': 5, 'long_window': 10}
    )
    first_run_time = time.time() - start_time
    
    # 두 번째 실행 (캐시 있음)
    start_time = time.time()
    run_backtest(
        df=sample_data,
        strategy_name='sma',
        initial_capital=10000000,
        params={'short_window': 5, 'long_window': 10}
    )
    second_run_time = time.time() - start_time
    
    # 캐시된 실행이 더 빨라야 함
    assert second_run_time < first_run_time 