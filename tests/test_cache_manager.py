"""
캐시 매니저 테스트

캐시 관리 기능을 테스트하는 케이스를 제공합니다.
"""

import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.utils.cache_manager import CacheManager

@pytest.fixture
def cache_manager():
    """테스트용 캐시 매니저 생성"""
    # 테스트용 임시 디렉토리 사용
    cache_dir = "tests/temp_cache"
    manager = CacheManager(cache_dir)
    yield manager
    # 테스트 후 정리
    if os.path.exists(cache_dir):
        for file in os.listdir(cache_dir):
            os.remove(os.path.join(cache_dir, file))
        os.rmdir(cache_dir)

def test_cache_directory_creation(cache_manager):
    """캐시 디렉토리 생성 테스트"""
    assert os.path.exists(cache_manager.cache_dir)
    assert os.path.isdir(cache_manager.cache_dir)

def test_save_and_load_json(cache_manager):
    """JSON 데이터 저장 및 로드 테스트"""
    # 테스트 데이터
    test_data = {
        "test_key": "test_value",
        "numbers": [1, 2, 3],
        "nested": {"key": "value"}
    }
    
    # 캐시 키
    key_parts = {
        "type": "test",
        "id": 1
    }
    
    # 데이터 저장
    cache_path = cache_manager.save_to_cache(test_data, key_parts)
    assert os.path.exists(cache_path)
    
    # 데이터 로드
    loaded_data = cache_manager.load_from_cache(key_parts)
    assert loaded_data == test_data

def test_save_and_load_dataframe(cache_manager):
    """DataFrame 저장 및 로드 테스트"""
    # 테스트 데이터프레임 생성
    df = pd.DataFrame({
        'A': np.random.rand(5),
        'B': np.random.rand(5)
    })
    
    # 캐시 키
    key_parts = {
        "type": "test_df",
        "id": 1
    }
    
    # 데이터 저장
    cache_path = cache_manager.save_to_cache(df, key_parts, extension="parquet")
    assert os.path.exists(cache_path)
    assert os.path.exists(cache_path.replace(".parquet", ".meta.json"))
    
    # 데이터 로드
    loaded_df = cache_manager.load_from_cache(key_parts, extension="parquet")
    pd.testing.assert_frame_equal(df, loaded_df)

def test_cache_expiration(cache_manager):
    """캐시 만료 테스트"""
    # 테스트 데이터
    test_data = {"test": "value"}
    key_parts = {"type": "test"}
    
    # 데이터 저장 (1초 후 만료)
    cache_manager.save_to_cache(test_data, key_parts, max_age=timedelta(seconds=1))
    
    # 즉시 로드 (성공해야 함)
    assert cache_manager.load_from_cache(key_parts) == test_data
    
    # 1초 대기
    import time
    time.sleep(1.1)
    
    # 만료 후 로드 (None이어야 함)
    assert cache_manager.load_from_cache(key_parts) is None

def test_clear_cache(cache_manager):
    """캐시 정리 테스트"""
    # 여러 테스트 파일 생성
    for i in range(3):
        test_data = {"test": f"value_{i}"}
        key_parts = {"type": "test", "id": i}
        cache_manager.save_to_cache(test_data, key_parts)
    
    # 캐시 정리
    cache_manager.clear_cache()
    
    # 모든 파일이 삭제되었는지 확인
    assert len(os.listdir(cache_manager.cache_dir)) == 0

def test_invalid_cache_key(cache_manager):
    """잘못된 캐시 키 테스트"""
    # 존재하지 않는 키로 로드 시도
    result = cache_manager.load_from_cache({"invalid": "key"})
    assert result is None

def test_cache_key_generation(cache_manager):
    """캐시 키 생성 테스트"""
    # 동일한 데이터로 키 생성
    key_parts1 = {"a": 1, "b": 2}
    key_parts2 = {"b": 2, "a": 1}  # 순서가 다름
    
    key1 = cache_manager._generate_cache_key(key_parts1)
    key2 = cache_manager._generate_cache_key(key_parts2)
    
    # 순서가 달라도 동일한 키가 생성되어야 함
    assert key1 == key2 