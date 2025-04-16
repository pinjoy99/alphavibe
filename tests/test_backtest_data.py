"""
백테스팅 데이터 테스트

백테스팅 데이터 조회 및 캐싱 기능을 테스트하는 케이스를 제공합니다.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.api.upbit_api import get_backtest_data
from src.utils.cache_manager import CacheManager
import os

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

def test_get_backtest_data_caching():
    """백테스팅 데이터 캐싱 테스트"""
    # 첫 번째 데이터 조회
    df1 = get_backtest_data("BTC", "1d", "minute60")
    assert df1 is not None
    assert isinstance(df1, pd.DataFrame)
    
    # 두 번째 데이터 조회 (캐시에서 로드되어야 함)
    df2 = get_backtest_data("BTC", "1d", "minute60")
    assert df2 is not None
    assert isinstance(df2, pd.DataFrame)
    
    # 두 데이터프레임이 동일한지 확인
    pd.testing.assert_frame_equal(df1, df2)

def test_get_backtest_data_expiration():
    """백테스팅 데이터 만료 테스트"""
    # 데이터 조회
    df1 = get_backtest_data("BTC", "1d", "minute60")
    assert df1 is not None
    
    # 캐시 매니저로 직접 만료 확인
    cache_manager = CacheManager()
    cache_key = {
        "ticker": "BTC",
        "period": "1d",
        "interval": "minute60",
        "type": "backtest_data"
    }
    
    # 캐시가 존재하는지 확인
    cached_data = cache_manager.load_from_cache(cache_key, extension="parquet")
    assert cached_data is not None
    
    # 만료된 캐시로 로드 시도
    expired_data = cache_manager.load_from_cache(
        cache_key,
        extension="parquet",
        max_age=timedelta(seconds=0)  # 즉시 만료
    )
    assert expired_data is None

def test_get_backtest_data_invalid_params():
    """잘못된 파라미터 테스트"""
    # 존재하지 않는 코인
    df = get_backtest_data("INVALID", "1d", "minute60")
    assert df is None
    
    # 잘못된 기간
    df = get_backtest_data("BTC", "invalid", "minute60")
    assert df is None
    
    # 잘못된 간격
    df = get_backtest_data("BTC", "1d", "invalid")
    assert df is None

def test_get_backtest_data_different_params():
    """다른 파라미터로 데이터 조회 테스트"""
    # BTC 1일 데이터
    df_btc_1d = get_backtest_data("BTC", "1d", "minute60")
    assert df_btc_1d is not None
    
    # ETH 1일 데이터
    df_eth_1d = get_backtest_data("ETH", "1d", "minute60")
    assert df_eth_1d is not None
    
    # BTC 1주 데이터
    df_btc_1w = get_backtest_data("BTC", "1w", "minute60")
    assert df_btc_1w is not None
    
    # 데이터가 서로 다른지 확인
    assert not df_btc_1d.equals(df_eth_1d)
    assert not df_btc_1d.equals(df_btc_1w)

def test_get_backtest_data_columns():
    """데이터프레임 컬럼 테스트"""
    df = get_backtest_data("BTC", "1d", "minute60")
    assert df is not None
    
    # 필수 컬럼 확인
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    assert all(col in df.columns for col in required_columns)
    
    # 데이터 타입 확인
    assert df['Open'].dtype in [float, int]
    assert df['High'].dtype in [float, int]
    assert df['Low'].dtype in [float, int]
    assert df['Close'].dtype in [float, int]
    assert df['Volume'].dtype in [float, int] 