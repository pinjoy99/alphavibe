"""
파일 및 경로 관련 유틸리티 함수 모듈
"""
import os
import json
from typing import Any, Dict, Optional
from datetime import datetime

def ensure_directory(directory: str) -> str:
    """
    디렉토리가 존재하는지 확인하고 없으면 생성
    
    Parameters:
        directory (str): 확인할 디렉토리 경로
        
    Returns:
        str: 생성된 디렉토리 절대 경로
    """
    # 상대 경로를 절대 경로로 변환
    if not os.path.isabs(directory):
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        directory = os.path.join(script_dir, directory)
    
    # 디렉토리가 없으면 생성
    os.makedirs(directory, exist_ok=True)
    
    return directory

def save_json(data: Dict[str, Any], file_path: str, ensure_dir: bool = True) -> str:
    """
    데이터를 JSON 파일로 저장
    
    Parameters:
        data (Dict[str, Any]): 저장할 데이터 딕셔너리
        file_path (str): 저장할 파일 경로
        ensure_dir (bool): 디렉토리 존재 확인 및 생성 여부
        
    Returns:
        str: 저장된 파일 경로
    """
    # 디렉토리 확인 및 생성
    if ensure_dir:
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory(directory)
    
    # JSON 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return file_path

def load_json(file_path: str) -> Optional[Dict[str, Any]]:
    """
    JSON 파일에서 데이터 로드
    
    Parameters:
        file_path (str): 로드할 파일 경로
        
    Returns:
        Optional[Dict[str, Any]]: 로드된 데이터 또는 파일이 없는 경우 None
    """
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_filename(prefix: str, name: str, suffix: Optional[str] = None, 
                      extension: str = 'json') -> str:
    """
    파일 이름 생성 (날짜 포함)
    
    Parameters:
        prefix (str): 파일 이름 접두사
        name (str): 파일 이름 중간 부분
        suffix (Optional[str]): 파일 이름 접미사
        extension (str): 파일 확장자 (기본값: json)
        
    Returns:
        str: 생성된 파일 이름
    """
    current_date = datetime.now().strftime("%Y%m%d")
    
    if suffix:
        return f"{prefix}_{name}_{suffix}_{current_date}.{extension}"
    else:
        return f"{prefix}_{name}_{current_date}.{extension}" 