"""
캐시 관리 모듈

데이터 캐싱을 위한 유틸리티 클래스와 함수를 제공합니다.
"""

import os
import json
import pandas as pd
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """데이터 캐싱을 관리하는 클래스"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Parameters:
            cache_dir (str): 캐시 디렉토리 경로
        """
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """캐시 디렉토리가 존재하는지 확인하고 없으면 생성"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
    def _generate_cache_key(self, key_parts: Dict[str, Any]) -> str:
        """
        캐시 키 생성
        
        Parameters:
            key_parts (Dict[str, Any]): 캐시 키를 구성하는 요소들
            
        Returns:
            str: 생성된 캐시 키
        """
        # 딕셔너리를 정렬된 문자열로 변환
        sorted_items = sorted(key_parts.items())
        key_string = json.dumps(sorted_items, sort_keys=True)
        
        # MD5 해시 생성
        return hashlib.md5(key_string.encode()).hexdigest()
        
    def get_cache_path(self, cache_key: str, extension: str = "json") -> str:
        """
        캐시 파일 경로 생성
        
        Parameters:
            cache_key (str): 캐시 키
            extension (str): 파일 확장자
            
        Returns:
            str: 캐시 파일 경로
        """
        return os.path.join(self.cache_dir, f"{cache_key}.{extension}")
        
    def save_to_cache(self, data: Union[Dict[str, Any], pd.DataFrame], 
                     key_parts: Dict[str, Any], 
                     extension: str = "json",
                     max_age: Optional[timedelta] = None) -> str:
        """
        데이터를 캐시에 저장
        
        Parameters:
            data (Union[Dict[str, Any], pd.DataFrame]): 저장할 데이터
            key_parts (Dict[str, Any]): 캐시 키 구성 요소
            extension (str): 파일 확장자
            max_age (Optional[timedelta]): 캐시 최대 유효 기간
            
        Returns:
            str: 저장된 캐시 파일 경로
        """
        try:
            # 캐시 키 생성
            cache_key = self._generate_cache_key(key_parts)
            cache_path = self.get_cache_path(cache_key, extension)
            
            # 메타데이터 생성
            metadata = {
                "created_at": datetime.now().isoformat(),
                "max_age": max_age.total_seconds() if max_age else None,
                "key_parts": key_parts
            }
            
            # 데이터 저장
            if isinstance(data, pd.DataFrame):
                # DataFrame을 parquet 형식으로 저장
                data.to_parquet(cache_path)
                # 메타데이터는 별도 파일로 저장
                metadata_path = self.get_cache_path(cache_key, "meta.json")
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            else:
                # 딕셔너리를 JSON으로 저장
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "data": data,
                        "metadata": metadata
                    }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"캐시 저장 완료: {cache_path}")
            return cache_path
            
        except Exception as e:
            logger.error(f"캐시 저장 중 에러 발생: {str(e)}")
            raise
            
    def load_from_cache(self, key_parts: Dict[str, Any], 
                       extension: str = "json",
                       max_age: Optional[timedelta] = None) -> Optional[Union[Dict[str, Any], pd.DataFrame]]:
        """
        캐시에서 데이터 로드
        
        Parameters:
            key_parts (Dict[str, Any]): 캐시 키 구성 요소
            extension (str): 파일 확장자
            max_age (Optional[timedelta]): 캐시 최대 유효 기간
            
        Returns:
            Optional[Union[Dict[str, Any], pd.DataFrame]]: 로드된 데이터 또는 None
        """
        try:
            # 캐시 키 생성
            cache_key = self._generate_cache_key(key_parts)
            cache_path = self.get_cache_path(cache_key, extension)
            
            # 캐시 파일이 없으면 None 반환
            if not os.path.exists(cache_path):
                return None
                
            # 메타데이터 확인
            if extension == "parquet":
                metadata_path = self.get_cache_path(cache_key, "meta.json")
                if not os.path.exists(metadata_path):
                    return None
                    
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    metadata = cached_data.get("metadata", {})
            
            # 캐시 유효성 검사
            created_at = datetime.fromisoformat(metadata["created_at"])
            cache_age = datetime.now() - created_at
            
            # 최대 유효 기간 확인
            if max_age and cache_age > max_age:
                logger.info(f"캐시가 만료됨: {cache_path}")
                return None
                
            # 데이터 로드
            if extension == "parquet":
                data = pd.read_parquet(cache_path)
            else:
                data = cached_data.get("data")
            
            logger.info(f"캐시 로드 완료: {cache_path}")
            return data
            
        except Exception as e:
            logger.error(f"캐시 로드 중 에러 발생: {str(e)}")
            return None
            
    def clear_cache(self, max_age: Optional[timedelta] = None):
        """
        캐시 정리
        
        Parameters:
            max_age (Optional[timedelta]): 삭제할 캐시의 최대 유효 기간
        """
        try:
            now = datetime.now()
            
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                
                # 메타데이터 파일은 건너뛰기
                if filename.endswith(".meta.json"):
                    continue
                    
                # 파일 생성 시간 확인
                created_time = datetime.fromtimestamp(os.path.getctime(file_path))
                file_age = now - created_time
                
                # 최대 유효 기간이 지난 파일 삭제
                if max_age and file_age > max_age:
                    os.remove(file_path)
                    # 메타데이터 파일도 삭제
                    meta_path = file_path.replace(".parquet", ".meta.json")
                    if os.path.exists(meta_path):
                        os.remove(meta_path)
                        
            logger.info("캐시 정리 완료")
            
        except Exception as e:
            logger.error(f"캐시 정리 중 에러 발생: {str(e)}")
            raise 